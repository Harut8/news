import asyncio
import datetime
from datetime import timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crawler.exception import UrlExistsError
from src.app.scheduler.dto import SchedulerDto, SchedulerStatusType, TaskDataDto
from src.app.scheduler.model import ScheduledUrl
from src.app.scheduler.repo import SchedulerRepository
from src.app.worker.dto import FetchUrlDto
from src.app.worker.events import RabbitMQEvents
from src.core.db.pg_uow import PgSQLAlchemyUnitOfWork
from src.core.rmq.rmq_publisher import RabbitMQPublisher
from src.core.utils.api.logger import LOGGER
from src.core.utils.base_value_objects import UrlString
from src.core.utils.repeat_at import repeat_at


class SchedulerService:
    def __init__(
        self,
        uow: PgSQLAlchemyUnitOfWork,
        rmq_publisher: RabbitMQPublisher,
    ):
        self._uow = uow
        self._rmq_publisher = rmq_publisher

    @staticmethod
    def current_time_plus_minute(x: int):
        _current_time = datetime.datetime.now(tz=timezone.utc)
        return _current_time + datetime.timedelta(minutes=x)

    async def is_unique_url(self, url: UrlString, session: AsyncSession, with_exception=True):
        _is_exists = await self._uow.get_repository(SchedulerRepository, session).is_url_exists(url)
        if _is_exists and with_exception:
            raise UrlExistsError(f"Url {url} already exists in scheduler")
        return _is_exists

    async def add_scheduled_url(self, url: UrlString):
        _schedule = SchedulerDto(
            url=url,
            task_data=TaskDataDto(
                routing_key=RabbitMQEvents.fetch_url.routing_key,
                exchange=RabbitMQEvents.fetch_url.exchange,
                queue=RabbitMQEvents.fetch_url.queue,
            ),
            status=SchedulerStatusType.PENDING,
            scheduled_time=SchedulerService.current_time_plus_minute(1),
        )
        _scheduler: ScheduledUrl = ScheduledUrl.factory(**_schedule.model_dump())
        async with self._uow.atomic() as _session:
            _is_exists = await self.is_unique_url(_scheduler.url, _session, with_exception=False)
            if _is_exists:
                LOGGER.info(f"Url {_scheduler.url} already exists")
                return
            await self._uow.get_repository(SchedulerRepository, _session).add_scheduled_url(_scheduler)

    async def fetch_10_pending_scheduled_urls_mark_as_processing(self) -> list[dict]:
        async with self._uow.atomic(read_only=True) as _session:
            _schedules = await self._uow.get_repository(
                SchedulerRepository, _session
            ).fetch_10_pending_scheduled_urls_mark_as_processing()
        return _schedules

    async def update_scheduled_url_status_by_id(
        self,
        schedule_id: int,
        status: SchedulerStatusType,
        retry_count: int,
        exception=None,
        schedule_time: Optional[datetime] = None,
    ):
        async with self._uow.atomic() as _session:
            await self._uow.get_repository(SchedulerRepository, _session).update_scheduled_url_status_by_id(
                schedule_id,
                {"status": status, "exception": exception, "retry_count": retry_count, "scheduled_time": schedule_time},
            )
            LOGGER.info(f"ScheduledUrl with id {schedule_id} status updated to {status}")

    async def _process_scheduled_url(
        self,
        schedule_id: int,
        retry_count: int,
        task_data: TaskDataDto,
        url: UrlString,
    ):
        if retry_count > 3:
            await self.update_scheduled_url_status_by_id(
                schedule_id=schedule_id,
                status=SchedulerStatusType.FAILED,
                retry_count=retry_count,
                exception="Max retry count exceeded",
            )
            LOGGER.error(f"ScheduledUrl with id {schedule_id} failed")
            return
        try:
            await self._rmq_publisher.publish(
                message=FetchUrlDto(url=url),
                routing_key=task_data.routing_key,
                exchange_name=task_data.exchange,
            )
        except Exception as e:
            LOGGER.error(f"ScheduledUrl with id {schedule_id} failed")
            await self.update_scheduled_url_status_by_id(
                schedule_id=schedule_id, status=SchedulerStatusType.PENDING, retry_count=retry_count + 1, exception=e
            )
        else:
            await self.update_scheduled_url_status_by_id(
                schedule_id=schedule_id, status=SchedulerStatusType.COMPLETED, retry_count=retry_count
            )

    async def process_scheduled_urls(self):
        _schedules = await self.fetch_10_pending_scheduled_urls_mark_as_processing()
        _tasks = [
            self._process_scheduled_url(
                schedule_id=schedule["id"],
                retry_count=schedule["retry_count"],
                task_data=TaskDataDto.model_validate(schedule["task_data"]),
                url=schedule["url"],
            )
            for schedule in _schedules
        ]
        await asyncio.gather(*_tasks)

    @repeat_at(cron="*/5 * * * *")
    async def start_scheduled_url_fetcher(self):
        LOGGER.info("Scheduled URL Fetcher Started")
        await self.process_scheduled_urls()

    async def update_predefined_url_status_by_id(
        self, schedule_id: int, retry_count: int, status: SchedulerStatusType, exception=None
    ):
        async with self._uow.atomic() as _session:
            await self._uow.get_repository(SchedulerRepository, _session).update_predefined_url_status_by_id(
                schedule_id, {"status": status, "exception": exception, "retry_count": retry_count}
            )
            LOGGER.info(f"PredefinedUrl with id {schedule_id} status updated to {status}")

    async def fetch_10_pending_predefined_urls_mark_as_processing(self):
        async with self._uow.atomic(read_only=True) as _session:
            _schedules = await self._uow.get_repository(
                SchedulerRepository, _session
            ).fetch_10_pending_predefined_urls_mark_as_processing()
        return _schedules

    async def _process_predefined_url(self, schedule_id: int, retry_count: int, url: UrlString, task_data: TaskDataDto):
        if retry_count > 3:
            await self.update_predefined_url_status_by_id(
                schedule_id, retry_count, SchedulerStatusType.FAILED, "Max retry count exceeded"
            )
            LOGGER.error(f"PredefinedUrl with id {schedule_id} failed")
            return
        try:
            await self._rmq_publisher.publish(
                message=FetchUrlDto(url=url),
                routing_key=task_data.routing_key,
                exchange_name=task_data.exchange,
            )
        except Exception as e:
            LOGGER.error(f"PredefinedUrl with id {schedule_id} failed")
            await self.update_predefined_url_status_by_id(schedule_id, retry_count + 1, SchedulerStatusType.PENDING, e)
        else:
            await self.update_predefined_url_status_by_id(schedule_id, retry_count, SchedulerStatusType.COMPLETED)

    async def process_predefined_urls(self):
        _schedules = await self.fetch_10_pending_predefined_urls_mark_as_processing()
        _tasks = [
            self._process_predefined_url(
                schedule_id=schedule["id"],
                retry_count=schedule["retry_count"],
                url=schedule["url"],
                task_data=TaskDataDto.model_validate(schedule["task_data"]),
            )
            for schedule in _schedules
        ]
        await asyncio.gather(*_tasks)

    @repeat_at(cron="*/10 * * * *")
    async def start_predefined_url_fetcher(self):
        LOGGER.info("Predefined URL Fetcher Started")
        await self.process_predefined_urls()
