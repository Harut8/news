import asyncio
import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.crawler.dto import AuthorDto, ContentDto, IndexDto, MetaDto
from src.app.crawler.exception import UrlExistsError
from src.app.crawler.model import Author, Content, CrawlingStatus, Index, Meta, Url
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
        self._keywords = {"a", "b"}  # TODO: Move to db

    async def is_unique_url(self, url: UrlString, session: AsyncSession, with_exception=True):
        _is_exists = await self._uow.get_repository(UrlRepository, session).is_url_exists(url)
        if _is_exists and with_exception:
            raise UrlExistsError(f"Url {url} already exists")
        return _is_exists

    async def add_url(self, url: UrlString) -> Url:
        async with self._uow.atomic() as session:
            _url = await self._uow.get_repository(UrlRepository, session).get_url(url)
            if _url:
                LOGGER.info(f"Url {url} already exists in URL table")
                return _url
            return await self._uow.get_repository(UrlRepository, session).add_url(
                Url.factory(url=url, status=CrawlingStatus.QUEUED.str_value)
            )

    async def _parse_content(self, data: str) -> ContentDto:
        ...

    async def _parse_meta(self, data: str) -> MetaDto:
        ...

    async def _parse_author(self, data: str) -> AuthorDto:
        ...

    async def _get_keyword_frequency(self, data: str) -> list[IndexDto]:
        _keyword_to_frequency: list[IndexDto] = []
        for _keyword in self._keywords:
            # TODO: Find frequency in effective way + parallel
            ...
        return _keyword_to_frequency

    async def _parse_index(self, data: str) -> list[IndexDto]:
        return await self._get_keyword_frequency(data)

    async def add_additional_data_to_url(self, url: Url, data: str):
        _content: ContentDto = await self._parse_content(data)  # TODO: May be parallel bottom 3
        _meta: MetaDto = await self._parse_meta(data)
        _author: AuthorDto = await self._parse_author(data)
        _indexes: list[IndexDto] = await self._parse_index(data)
        async with self._uow.atomic() as session:
            url.content = Content.factory(**_content.model_dump())
            url.author = Author.factory(**_author.model_dump())
            url.meta = Meta.factory(**_author.model_dump())
            url.index = [Index.factory(**_index.model_dump()) for _index in _indexes]
            await self._uow.get_repository(UrlRepository, session).add_url(url)

    async def find_sub_urls(self, url_id: URL_ID):
        ...


class FetchingService:
    def __init__(self, uow: PgSQLAlchemyUnitOfWork, scraper: Any):
        self._uow = uow
        self._scraper = scraper

    async def fetch_info_from_url(self, url: Url) -> str:
        LOGGER.info(f"Fetching info from url {url.id}")
        _data: str = await self._scraper.scrape_data(url.url)  # TODO: This should be fault tolerant
        async with self._uow.atomic() as session:
            await self._uow.get_repository(UrlRepository, session).update_url(
                url_id=URL_ID(url.id),
                kwargs={
                    "crawled_at": datetime.datetime.now(tz=datetime.timezone.utc),
                },
            )
        return _data


class CrawlerService:
    def __init__(
        self, parsing_service: ParsingService, fetching_service: FetchingService, scheduler_service: SchedulerService
    ):
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
        await asyncio.sleep(3)
        _url = await self._parsing_service.add_url(url)
        _data = await self._fetching_service.fetch_info_from_url(_url)
        await self._parsing_service.add_additional_data_to_url(_url, _data)
