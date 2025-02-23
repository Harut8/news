import asyncio
from asyncio import ensure_future
from datetime import datetime
from functools import wraps

from croniter import croniter
from starlette.concurrency import run_in_threadpool

from src.core.utils.api.logger import LOGGER


def get_delta(cron):
    now = datetime.now()
    cron = croniter(cron, now)
    return (cron.get_next(datetime) - now).total_seconds()
    # return 10


def repeat_at(*, cron: str, max_repetitions: int | None = None) -> callable:
    def decorator(func):
        is_coroutine = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            repetitions = 0
            if not croniter.is_valid(cron):
                raise ValueError(f"Invalid cron expression: {cron}")

            async def loop(*args, **kwargs):
                nonlocal repetitions
                while max_repetitions is None or repetitions < max_repetitions:
                    try:
                        sleep_time = get_delta(cron)
                        await asyncio.sleep(sleep_time)
                        if is_coroutine:
                            await func(*args, **kwargs)
                        else:
                            await run_in_threadpool(func, *args, **kwargs)
                        LOGGER.debug(f"Task executed successfully. Repetition: {repetitions}")
                    except Exception as e:
                        LOGGER.error(f"Error executing task: {str(e)}", exc_info=True)
                    repetitions += 1
                LOGGER.info(f"Task completed after {repetitions} repetitions")

            task = ensure_future(loop(*args, **kwargs))
            return task

        return wrapper

    return decorator
