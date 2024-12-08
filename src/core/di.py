from dependency_injector import containers, providers
from dependency_injector.providers import Singleton

from src.app.user.repo import UserRepository
from src.app.user.service import UserService
from src.core.db.pg_base_repo import BaseRepository
from src.core.db.pg_connection import PgAsyncSQLAlchemyAdapter
from src.core.db.pg_uow import PgSQLAlchemyUnitOfWork
from src.core.utils.api.logger import LOGGER


class DependencyContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.core.utils.api.middlewares",
            "src.app.user.bot_api",
        ]
    )

    pg_db: Singleton[PgAsyncSQLAlchemyAdapter] = providers.Singleton(
        PgAsyncSQLAlchemyAdapter,
        url=config.DATABASE.DATABASE_URL,
        echo=config.DATABASE.DEBUG,
        logger=LOGGER,
    )
    uow: PgSQLAlchemyUnitOfWork = providers.Singleton(
        PgSQLAlchemyUnitOfWork,
        sqlalchemy_adapter=pg_db,
        logger=LOGGER,
        repositories={
            BaseRepository.__name__: BaseRepository,
            UserRepository.__name__: UserRepository,
        },
    )
    user_service: UserService = providers.Factory(
        UserService,
        uow=uow,
    )
