from asyncio import current_task
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)


class PgAsyncSQLAlchemyAdapter:
    def __init__(self, url: str, echo: bool = False, logger=None) -> None:
        self._url = url
        self._echo = echo
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._async_scoped_session = None
        self._logger = logger
        self.connect()

    async def dispose(self):
        if self._engine:
            await self._engine.dispose()

    def connect(self):
        self._engine = create_async_engine(
            url=self._url,
            echo=self._echo,
            pool_size=10,
            max_overflow=50,
            future=True,
            pool_timeout=10,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
        self._async_scoped_session = async_scoped_session(
            session_factory=self._session_factory,
            scopefunc=current_task,
        )

        if self._logger:
            self._logger.info("Connected to database")

    @property
    def async_scoped_session(self) -> async_scoped_session:
        return self._async_scoped_session

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory
