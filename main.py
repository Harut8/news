import logging
import sys
from contextlib import asynccontextmanager

import uvloop
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from src.app.crawler.rest_api import crawler_router
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


class CustomFastAPI(FastAPI):
    container: DependencyContainer



@asynccontextmanager
async def lifespan(_app: CustomFastAPI):
    try:
        async with _app.container.pg_db.provided.engine().begin() as _conn:
            await _conn.execute(text("SET lock_timeout = '4s'"))
            await _conn.execute(text("SET statement_timeout = '8s'"))
        await _app.container.rmq_broker.provided.connect()()
        await _app.container.scheduler_service.provided.start_scheduler()()
    except Exception as _e:
        LOGGER.exception(_e)
    yield


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
    _app.include_router(
        crawler_router,
        prefix=f"{SETTINGS.API_V1.API_V1_PREFIX}/crawler",
        tags=["crawler"],
    )
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

@fastapi_app.get("/health")
async def health():
    return {"status": "ok"}


@fastapi_app.get("/ready")
async def ready():
    return {"status": "ok"}