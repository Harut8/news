from sqlalchemy import select, update

from src.app.crawler.model import Author, Content, Index, Meta, Url
from src.core.db.pg_base_repo import BaseRepository
from src.core.utils.types import URL_ID


class UrlRepository(BaseRepository[Url]):
    async def add_url(self, url: Url) -> Url:
        return await self.insert_one_with_commit(url)

    async def add_urls(self, urls: list[Url]) -> list[Url]:
        return await self.bulk_insert_orm_without_commit(urls)

    async def is_url_exists(self, url: str) -> bool:
        _stmt = select(Url).filter(Url.url.ilike(url))
        return True if await self.run_select_stmt_for_one(_stmt) else False

    async def update_url(self, url_id: URL_ID, kwargs: dict) -> Url:
        _stmt = update(Url).where(Url.id == url_id).values(**kwargs)
        return await self.update_stmt_without_commit(_stmt)

    async def get_url(self, url: str) -> Url:
        _stmt = select(Url).filter(Url.url.ilike(url))
        return await self.run_select_stmt_for_one(_stmt)


class IndexRepository(BaseRepository[Index]):
    ...


class ContentRepository(BaseRepository[Content]):
    ...


class MetaRepository(BaseRepository[Meta]):
    ...


class AuthorRepository(BaseRepository[Author]):
    ...
