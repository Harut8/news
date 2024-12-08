import logging
import sys
from contextlib import asynccontextmanager
from os import getppid

import uvloop
from aiogram.types import WebhookInfo
from aiogram import types
from aiogram import Bot, Dispatcher
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from src.app.user.bot_api import user_router
from src.core.conf.settings import SETTINGS
from src.core.di import DependencyContainer
from src.core.utils.api.http_exceptions import (
    NotFound,
    ValidationError,
    pydantic_error_to_str,
    ServiceException,
)
from src.core.utils.api.logger import LOGGER, RouterLoggingMiddleware

uvloop.install()

PPID_STORE = {}


async def is_first_run() -> bool:
    _ppid = getppid()
    if _ppid and PPID_STORE.get("tg_bot_ppid") == _ppid:
        return False
    PPID_STORE["tg_bot_ppid"] = _ppid
    return True


class CustomFastAPI(FastAPI):
    container: DependencyContainer


async def start_telegram(app: CustomFastAPI) -> None:
    _fr = await is_first_run()
    LOGGER.debug(f"First run: {_fr}")
    if _fr:
        await set_webhook(app.container.bot)


@asynccontextmanager
async def lifespan(_app: CustomFastAPI):
    try:
        await start_telegram(_app)
        async with _app.container.pg_db.provided.engine().begin() as _conn:
            await _conn.execute(text("SET lock_timeout = '4s'"))
            await _conn.execute(text("SET statement_timeout = '8s'"))
    except Exception as _e:
        LOGGER.exception(_e)
    yield


async def set_webhook(my_bot: Bot) -> None:
    async def check_webhook() -> WebhookInfo:
        try:
            _webhook_info = await my_bot.get_webhook_info()
            return _webhook_info
        except Exception as _e:
            raise _e from None

    _current_webhook_info = await check_webhook()
    LOGGER.debug(f"Current bot info: {_current_webhook_info}")
    try:
        # todo: add secret token + checking in webhook
        await my_bot.set_webhook(
            f"{SETTINGS.API_V1.API_BASE_URL}{SETTINGS.Tg.WEBHOOK_PATH}",
            drop_pending_updates=_current_webhook_info.pending_update_count > 0,
            max_connections=40 if SETTINGS.APP_SETTINGS.DEBUG else 100,
        )
        LOGGER.debug(f"Updated bot info: {await check_webhook()}")
    except Exception as e:
        raise e from None


def create_app() -> CustomFastAPI:
    origins: set = {
        "*",
        "http://localhost",
        "http://localhost:*",
        "http://localhost:3000",
    }
    _app = CustomFastAPI(
        lifespan=lifespan,
        root_path="/carumi",
        docs_url="/swagger",
    )
    _app.container = DependencyContainer()
    _app.container.config.from_dict(SETTINGS.model_dump())
    LOGGER.setLevel(SETTINGS.APP_SETTINGS.LOG_LEVEL)
    logging.getLogger("httpx").setLevel(SETTINGS.APP_SETTINGS.LOG_LEVEL)
    logging.getLogger("sqlalchemy.engine").setLevel(SETTINGS.APP_SETTINGS.LOG_LEVEL)
    _app.container.wire(modules=[sys.modules[__name__]])
    _app.container.init_resources()
    _app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _app.add_middleware(
        RouterLoggingMiddleware,  # type: ignore
        app_logger=LOGGER,
    )
    _tg_dp = Dispatcher()
    _tg_dp.include_router(user_router)
    _BOT = Bot(token=SETTINGS.Tg.BOT_TOKEN.get_secret_value())
    _app.container.bot = _BOT
    _app.container.dp = _tg_dp
    return _app


fastapi_app = create_app()


@fastapi_app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return NotFound(**exc.detail).to_response()
    return NotFound(message=f"{exc} : {request.url}").to_response()


@fastapi_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: HTTPException):
    return ValidationError(
        message=f"{pydantic_error_to_str(exc)} : {request.url}"
    ).to_response()


@fastapi_app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    return ServiceException().to_response()


@fastapi_app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return HTMLResponse("<h1 style='color: red'>Hello World</h1>")


@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}


@fastapi_app.get("/ready")
async def ready():
    return {"status": "ok"}


@fastapi_app.post(SETTINGS.Tg.WEBHOOK_PATH)
async def bot_webhook(update: dict) -> None:
    _telegram_update = types.Update(**update)
    await fastapi_app.container.dp.feed_webhook_update(
        bot=fastapi_app.container.bot, update=_telegram_update
    )
