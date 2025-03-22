from dependency_injector import containers, providers
from dependency_injector.providers import Factory, Singleton
from faststream.asgi import AsgiFastStream
from faststream.rabbit import RabbitBroker, RabbitRouter

from src.app.crawler.fake_scrapper import FakeCrawler
from src.app.crawler.repo import ContentRepository, IndexRepository, MetaRepository, UrlRepository
from src.app.crawler.service import CrawlerService, FetchingService, ParsingService
from src.app.scheduler.repo import SchedulerRepository
from src.app.scheduler.service import SchedulerService
from src.core.db.pg_base_repo import BaseRepository
from src.core.db.pg_connection import PgAsyncSQLAlchemyAdapter
from src.core.db.pg_uow import PgSQLAlchemyUnitOfWork
from src.core.rmq.rmq_publisher import RabbitMQPublisher
from src.core.utils.api.logger import LOGGER


class DependencyContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.core.utils.api.middlewares",
            "src.app.crawler.rest_api",
        ]
    )

    pg_db: Singleton[PgAsyncSQLAlchemyAdapter] = providers.Singleton(
        PgAsyncSQLAlchemyAdapter,
        url=config.DATABASE.DATABASE_URL,
        echo=config.DATABASE.DEBUG,
        logger=LOGGER,
    )
    rmq_broker: Singleton[RabbitBroker] = providers.Singleton(
        RabbitBroker,
        url=config.RABBITMQ.BROKER_URL,
        # security=security,
    )
    rmq_router = providers.Singleton(
        RabbitRouter,
        config.RABBITMQ.BROKER_URL,
    )
    rmq_publisher = providers.Singleton(RabbitMQPublisher, broker_adapter=rmq_broker, logger=LOGGER)

    uow: PgSQLAlchemyUnitOfWork = providers.Singleton(
        PgSQLAlchemyUnitOfWork,
        sqlalchemy_adapter=pg_db,
        logger=LOGGER,
        repositories={
            BaseRepository.__name__: BaseRepository,
            IndexRepository.__name__: IndexRepository,
            ContentRepository.__name__: ContentRepository,
            UrlRepository.__name__: UrlRepository,
            MetaRepository.__name__: MetaRepository,
            SchedulerRepository.__name__: SchedulerRepository,
        },
    )
    faststream_app = providers.Singleton(AsgiFastStream, rmq_broker)

    parsing_service: Factory[ParsingService] = providers.Factory(ParsingService, uow=uow, scraper=FakeCrawler())
    fetching_service: Factory[CrawlerService] = providers.Factory(FetchingService, uow=uow, scraper=FakeCrawler())
    scheduler_service: Factory[SchedulerService] = providers.Factory(SchedulerService, uow=uow, rmq_publisher=rmq_publisher)

    crawling_service: Factory[CrawlerService] = providers.Factory(
        CrawlerService, fetching_service=fetching_service, scheduler_service=scheduler_service, parsing_service=parsing_service
    )
