import json
from functools import wraps
from typing import Any, Callable, Dict, Tuple

import circuitbreaker
import httpx
from retry_async import retry

from src.core.utils.api.http_exceptions import (
    ServiceUnavailableException,
    TimeoutException,
    RequestError,
    BadGatewayException,
)
from src.core.utils.api.logger import LOGGER

CACHE: Dict[Tuple[str, str], Any] = {}  # todo: move to redis or memcache


def cache_request(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(*args, **kwargs):
        cache_key = (
            kwargs.get("url", ""),
            json.dumps(kwargs.get("params", {}), sort_keys=True),
        )
        if kwargs.get("cache", 0) == 1:
            if cache_key in CACHE:
                LOGGER.info(f"Returning from cache: {cache_key}")
                return CACHE[cache_key]
        response = await func(*args, **kwargs)
        if kwargs.get("cache", 0) == 1:
            LOGGER.info("Returning as normal request")
            CACHE[cache_key] = response
        return response

    return wrapper


def handle_circuit_breaker_exception(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except circuitbreaker.CircuitBreakerError as e:
            raise ServiceUnavailableException(
                message="Service Unavailable due to Circuit Breaker"
            ) from e

    return wrapper


class CustomCircuitBreaker(circuitbreaker.CircuitBreaker):
    FAILURE_THRESHOLD = 3
    RECOVERY_TIMEOUT = 5
    EXPECTED_EXCEPTION = Exception


def request_exception_handler(func: Callable[..., Any]) -> Callable[..., Any]:
    @CustomCircuitBreaker()
    @retry(
        exceptions=(ServiceUnavailableException, BadGatewayException, TimeoutException),
        tries=3,
        delay=2,
        backoff=1,
        is_async=True,
    )
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            raise RequestError(
                message=f"Something went wrong. Problem likes network issue or server error. REASON: {e}",
            ) from e
        except httpx.ConnectError as e:
            raise ServiceUnavailableException(
                message="Third Service Unavailable"
            ) from e
        except httpx.ConnectTimeout as e:
            raise TimeoutException(message="Connection Timeout") from e

    return wrapper


def run_request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with httpx.AsyncClient() as client:
            kwargs["client"] = client
            kwargs["timeout"] = 3  # this is in seconds
            response = await func(*args, **kwargs)
            response.raise_for_status()
            try:
                return response.json()
            except json.JSONDecodeError as e:
                LOGGER.exception(e)
                pass
            return response.status_code in [200, 201, 204]

    return wrapper


@handle_circuit_breaker_exception
@request_exception_handler
@run_request
@cache_request
async def create_get_request(url, client, base_url, cache=0, **kwargs):
    LOGGER.info(f"Making GET request to {base_url}{url}")
    return await client.get(f"{base_url}{url}", **kwargs)


@handle_circuit_breaker_exception
@request_exception_handler
@run_request
async def create_patch_request(url, client, base_url, data=None, **kwargs):
    LOGGER.info(f"Making PATCH request to {base_url}{url}")
    return (
        await client.patch(f"{base_url}{url}", data=json.dumps(data), **kwargs)
        if data
        else await client.patch(f"{base_url}{url}", **kwargs)
    )


@handle_circuit_breaker_exception
@request_exception_handler
@run_request
async def create_post_request(url, client, base_url, data=None, **kwargs):
    LOGGER.info(f"Making POST request to {base_url}{url}")
    return (
        await client.post(f"{base_url}{url}", data=json.dumps(data), **kwargs)
        if data
        else await client.post(f"{base_url}{url}", **kwargs)
    )


@handle_circuit_breaker_exception
@request_exception_handler
@run_request
async def create_delete_request(url, client, base_url, **kwargs):
    LOGGER.info(f"Making DELETE request to {base_url}{url}")
    return await client.delete(f"{base_url}{url}", **kwargs)
