from sqlalchemy import select

from src.app.crawler.model import Url, Index, Content, Meta, Author
from src.core.db.pg_base_repo import BaseRepository


class UrlRepository(BaseRepository[Url]):
    async def add_url(self, url: Url)-> Url:
        return await self.insert_one_with_commit(url)

    async def add_urls(self, urls: list[Url])-> list[Url]:
        return await self.bulk_insert_orm_without_commit(urls)

    async def is_url_exists(self, url: str)-> bool:
        _stmt = select(Url).filter(Url.url.ilike(url))
        return True if await self.run_select_stmt_for_one(_stmt) else False


class IndexRepository(BaseRepository[Index]):
    ...

class ContentRepository(BaseRepository[Content]):
    ...

class MetaRepository(BaseRepository[Meta]):
    ...

class AuthorRepository(BaseRepository[Author]):
    ...