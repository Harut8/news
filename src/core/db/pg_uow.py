import functools
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.pg_base_repo import BaseRepository
from src.core.db.pg_connection import PgAsyncSQLAlchemyAdapter

REPO = TypeVar("REPO", bound=BaseRepository)


class PgSQLAlchemyUnitOfWork:
    def __init__(
        self,
        sqlalchemy_adapter: PgAsyncSQLAlchemyAdapter,
        repositories: dict[str, REPO],
        logger: logging.Logger,
    ) -> None:
        self._sqlalchemy_adapter = sqlalchemy_adapter
        self._repositories = repositories
        self._logger = logger

    @property
    def sqlalchemy_adapter(self) -> PgAsyncSQLAlchemyAdapter:
        return self._sqlalchemy_adapter

    @asynccontextmanager
    async def atomic(self, read_only: bool = False) -> AsyncGenerator[AsyncSession | Any, Any]:
        async with self.sqlalchemy_adapter.async_scoped_session() as _session:
            try:
                if self._logger:
                    self._logger.debug(f"Session status: {_session.bind.pool.status()} at start")
                yield _session
                if not read_only:
                    await _session.commit()
            except Exception as e:
                await _session.rollback()
                raise e
            finally:
                await _session.close()
            if self._logger:
                self._logger.debug(f"Session status: {_session.bind.pool.status()} at end")

    @asynccontextmanager
    async def atomic_concurrent(self) -> AsyncGenerator[AsyncSession, Any]:
        async with self.sqlalchemy_adapter.engine.begin() as _conn:
            async with self.sqlalchemy_adapter.session_factory() as _session:
                try:
                    async with _session.begin():
                        if self._logger:
                            self._logger.debug(f"Session status: {_session.bind.pool.status()} at start")
                        yield _session
                except Exception as e:
                    await _session.rollback()
                    raise e
                if self._logger:
                    self._logger.debug(f"Session status: {_session.bind.pool.status()} at end")

    def transactional(self):
        def wrapper(func: Callable) -> Callable:
            @functools.wraps(func)
            async def wrapper_func(*args, **kwargs):
                async with self.atomic():
                    return await func(*args, **kwargs)

            return wrapper_func

        return wrapper

    async def dispose_uow(self):
        await self._sqlalchemy_adapter.dispose()

    def get_repository(self, repository: Type[REPO], session: AsyncSession) -> REPO:
        _founded_repo_class: Type[REPO] = self._repositories.get(repository.__name__)
        _repo = _founded_repo_class(session)
        return _repo
