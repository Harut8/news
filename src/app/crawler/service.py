import asyncio
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crawler.exception import UrlExistsError
from src.app.crawler.model import Url, CrawlingStatus
from src.app.crawler.repo import UrlRepository
from src.app.scheduler.service import SchedulerService
from src.core.db.pg_uow import PgSQLAlchemyUnitOfWork
from src.core.utils.api.logger import LOGGER
from src.core.utils.base_value_objects import UrlString
from src.core.utils.types import URL_ID


class ParsingService:
    def __init__(self, uow: PgSQLAlchemyUnitOfWork, scraper: Any):
        self._uow = uow
        self._scraper = scraper

    async def is_unique_url(self, url: UrlString, session: AsyncSession, with_exception=True):
        _is_exists = await self._uow.get_repository(UrlRepository, session).is_url_exists(url)
        if _is_exists and with_exception:
            raise UrlExistsError(f"Url {url} already exists")
        return _is_exists

    async def add_url(self, url: UrlString)->Optional[Url]:
        async with self._uow.atomic() as session:
            _is_exists = await self.is_unique_url(url, session, with_exception=False)
            if _is_exists:
                LOGGER.info(f"Url {url} already exists in URL table")
                return None
            return await self._uow.get_repository(UrlRepository, session).add_url(Url.factory(url=url, status=CrawlingStatus.QUEUED.str_value))

    async def find_sub_urls(self, url_id: URL_ID):
        ...

class FetchingService:
    def __init__(self, uow: PgSQLAlchemyUnitOfWork, scraper: Any):
        self._uow = uow
        self._scraper = scraper

    async def fetch_info_from_url(self, url_id: URL_ID):
        LOGGER.info(f"Fetching info from url {url_id}")

class CrawlerService:
    def __init__(self,
                 parsing_service: ParsingService,
                 fetching_service: FetchingService,
                 scheduler_service: SchedulerService):
        self._parsing_service = parsing_service
        self._fetching_service = fetching_service
        self._scheduler_service = scheduler_service

    async def test_fetching(self):
        await self._scheduler_service.fetch_10_pending_schedules_mark_as_processing()

    async def schedule_urls(self, urls: list[UrlString]):
        await asyncio.gather(*[self._scheduler_service.add_schedule(url) for url in urls])

    async def find_sub_urls(self, url: UrlString):
        return await self._parsing_service.find_sub_urls(url)

    async def fetch_info_from_url(self, url: UrlString):
        _url = await self._parsing_service.add_url(url)
        if not _url:
            return
        return await self._fetching_service.fetch_info_from_url(URL_ID(_url.id))