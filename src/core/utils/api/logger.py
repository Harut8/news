import logging.config
import sys
import time
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logging_config = {
    "version": 1,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(process)s %(levelname)s %(name)s",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": sys.stderr,
        }
    },
    "root": {"level": "DEBUG", "handlers": ["console"], "propagate": True},
}

logging.config.dictConfig(logging_config)

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))


class RouterLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, *, app_logger: logging.Logger) -> None:
        self._logger = app_logger
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id: str = str(uuid4())
        logging_dict = {
            "X-API-REQUEST-ID": request_id,
            "service": "Top Service",
        }

        _response_logging, response = await self._log_response(
            call_next, request, request_id
        )
        request_dict = await RouterLoggingMiddleware._log_request(request)
        logging_dict.update(request_dict)
        logging_dict.update(_response_logging)
        self._logger.info(logging_dict)
        return response

    @staticmethod
    async def _log_request(request: Request) -> dict:
        path = request.url.path
        if request.query_params:
            path += f"?{request.query_params}"
        request_logging = {
            "method": request.method,
            "path": path,
            "ip": request.client.host,
        }

        return request_logging

    async def _log_response(
        self, call_next: Callable, request: Request, request_id: str
    ):
        start_time = time.perf_counter()
        response = await self._execute_request(call_next, request, request_id)
        finish_time = time.perf_counter()
        overall_status = "successful" if response.status_code < 400 else "failed"
        execution_time = finish_time - start_time

        response_logging = {
            "request_function_name": request.scope.get("route").path
            if request.scope.get("route")
            else "unknown",
            "user_id": request.scope.get("X-User-ID"),
            "status": overall_status,
            "status_code": response.status_code,
            "time_taken": f"{execution_time:0.4f}s",
        }
        return response_logging, response

    async def _execute_request(
        self, call_next: Callable, request: Request, request_id: str
    ) -> Response:
        try:
            response: Response = await call_next(request)
            response.headers["X-API-Request-ID"] = request_id
            return response
        except Exception as e:
            self._logger.exception(
                {"path": request.url.path, "method": request.method, "reason": e}
            )
