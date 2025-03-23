from typing import Any, Awaitable, Callable

from faststream.rabbit import ExchangeType, RabbitExchange, RabbitMessage, RabbitQueue

from src.app.worker.dto import ByDateFetchUrlDto, FetchedUrlDto, FetchUrlDto
from src.app.worker.events import RabbitMQEvents
from src.core.conf.settings import SETTINGS
from src.core.di import DependencyContainer
from src.core.utils.api.logger import LOGGER

CONTAINER = DependencyContainer()
CONTAINER.config.from_dict(SETTINGS.model_dump())
rmq_broker = CONTAINER.rmq_broker()
consumer_app = CONTAINER.faststream_app()


@consumer_app.on_startup
async def startup():
    await rmq_broker.connect()
    await CONTAINER.scheduler_service().start_predefined_url_fetcher()


async def subscriber_middleware(
    call_next: Callable[[Any], Awaitable[Any]],
    msg: RabbitMessage,
) -> Any:
    return await call_next(msg)


###
# Dead letter


def _process_dead_letter_message(fn: Callable[[RabbitMessage], Awaitable[RabbitMessage]]):
    async def _decor(message: RabbitMessage):
        _deaf_header = message.headers.get("x-death")
        _count = _deaf_header[0].get("count")
        LOGGER.info(f"----Message received from dead letter queue----: {message.raw_message.routing_key} with count {_count}")
        if _count >= 3:
            LOGGER.info(f"Maximum retries reached for message: {message.raw_message.routing_key}")
            return
        await fn(message)

    return _decor


@rmq_broker.subscriber(
    RabbitQueue(
        RabbitMQEvents.fetch_url.queue_dead_letter,
        durable=True,
        routing_key=RabbitMQEvents.fetch_url.routing_key_dead_letter,
        arguments={
            "x-message-ttl": 3000,  # in ms
        },
    ),
    RabbitExchange(RabbitMQEvents.fetch_url.exchange_dead_letter, durable=True, type=ExchangeType.DIRECT),
    middlewares=[subscriber_middleware],  # type: ignore
)
@_process_dead_letter_message
async def fetch_info_from_url_dead_letter(message: RabbitMessage):
    await CONTAINER.rmq_publisher().publish(
        message.body,
        exchange_name=RabbitMQEvents.fetch_url.exchange,
        routing_key=RabbitMQEvents.fetch_url.routing_key,
        headers=message.headers,
    )
    LOGGER.info(f"---- Republished message to main queue ----: {RabbitMQEvents.fetch_url.routing_key}")


@rmq_broker.subscriber(
    RabbitQueue(
        RabbitMQEvents.content_fetched.queue_dead_letter,
        durable=True,
        routing_key=RabbitMQEvents.content_fetched.routing_key_dead_letter,
        arguments={
            "x-message-ttl": 3000,  # in ms
        },
    ),
    RabbitExchange(RabbitMQEvents.content_fetched.exchange_dead_letter, durable=True, type=ExchangeType.DIRECT),
    middlewares=[subscriber_middleware],  # type: ignore
)
@_process_dead_letter_message
async def content_fetched_dead_letter(message: RabbitMessage):
    await CONTAINER.rmq_publisher().publish(
        message.body,
        exchange_name=RabbitMQEvents.content_fetched.exchange,
        routing_key=RabbitMQEvents.content_fetched.routing_key,
        headers=message.headers,
    )


@rmq_broker.subscriber(
    RabbitQueue(
        RabbitMQEvents.check_sub_url_by_date.queue_dead_letter,
        durable=True,
        routing_key=RabbitMQEvents.check_sub_url_by_date.routing_key_dead_letter,
        arguments={
            "x-message-ttl": 3000,  # in ms
        },
    ),
    RabbitExchange(RabbitMQEvents.check_sub_url_by_date.exchange_dead_letter, durable=True, type=ExchangeType.DIRECT),
    middlewares=[subscriber_middleware],  # type: ignore
)
@_process_dead_letter_message
async def check_sub_url_dead_letter(message: RabbitMessage):
    await CONTAINER.rmq_publisher().publish(
        message.body,
        exchange_name=RabbitMQEvents.check_sub_url_by_date.exchange,
        routing_key=RabbitMQEvents.check_sub_url_by_date.routing_key,
        headers=message.headers,
    )


# End dead letter
###


@rmq_broker.subscriber(
    RabbitQueue(
        RabbitMQEvents.fetch_url.queue,
        durable=True,
        routing_key=RabbitMQEvents.fetch_url.routing_key,
        arguments={
            "x-dead-letter-exchange": RabbitMQEvents.fetch_url.exchange_dead_letter,
            "x-dead-letter-routing-key": RabbitMQEvents.fetch_url.routing_key_dead_letter,
        },
    ),
    RabbitExchange(RabbitMQEvents.fetch_url.exchange, durable=True, type=ExchangeType.DIRECT),
)
async def fetch_info_from_url(message: FetchUrlDto):
    LOGGER.info(f"----Message received----: {message}")
    _url = await CONTAINER.crawling_service().fetch_info_from_url(message.url)
    LOGGER.info(f"----Message processed----: {message}")
    await CONTAINER.rmq_publisher().publish(
        FetchedUrlDto(url_id=_url.id),
        exchange_name=RabbitMQEvents.content_fetched.exchange,
        routing_key=RabbitMQEvents.content_fetched.routing_key,
    )


@rmq_broker.subscriber(
    RabbitQueue(
        RabbitMQEvents.content_fetched.queue,
        durable=True,
        routing_key=RabbitMQEvents.content_fetched.routing_key,
        arguments={
            "x-dead-letter-exchange": RabbitMQEvents.content_fetched.exchange_dead_letter,
            "x-dead-letter-routing-key": RabbitMQEvents.content_fetched.routing_key_dead_letter,
        },
    ),
    RabbitExchange(RabbitMQEvents.content_fetched.exchange, durable=True, type=ExchangeType.DIRECT),
)
async def pass_fetched_content_through_llm(message: FetchedUrlDto):
    LOGGER.info(f"----Message received----: {message}")
    await CONTAINER.crawling_service().process_fetched_content(message.url_id)
    LOGGER.info(f"----Message processed----: {message}")


@rmq_broker.subscriber(
    RabbitQueue(
        RabbitMQEvents.check_sub_url_by_date.queue,
        durable=True,
        routing_key=RabbitMQEvents.check_sub_url_by_date.routing_key,
        arguments={
            "x-dead-letter-exchange": RabbitMQEvents.check_sub_url_by_date.exchange_dead_letter,
            "x-dead-letter-routing-key": RabbitMQEvents.check_sub_url_by_date.routing_key_dead_letter,
        },
    ),
    RabbitExchange(RabbitMQEvents.check_sub_url_by_date.exchange, durable=True, type=ExchangeType.DIRECT),
)
async def check_sub_url_by_date(message: ByDateFetchUrlDto):
    LOGGER.info(f"----Message received----: {message}")
    await CONTAINER.crawling_service().check_url_by_date_add_scheduled_url(message)
    LOGGER.info(f"----Message processed----: {message}")
