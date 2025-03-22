from typing import Any, Awaitable, Callable

from faststream.rabbit import ExchangeType, RabbitExchange, RabbitMessage, RabbitQueue

from src.app.worker.dto import FetchUrlDto
from src.app.worker.events import RabbitMQEvents
from src.core.conf.settings import SETTINGS
from src.core.di import DependencyContainer
from src.core.utils.api.logger import LOGGER

CONTAINER = DependencyContainer()
CONTAINER.config.from_dict(SETTINGS.model_dump())
rmq_broker = CONTAINER.rmq_broker()
consumer_app = CONTAINER.faststream_app()


async def subscriber_middleware(
    call_next: Callable[[Any], Awaitable[Any]],
    msg: RabbitMessage,
) -> Any:
    return await call_next(msg)


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
async def fetch_info_from_url_dead_letter(message: RabbitMessage):
    _deaf_header = message.headers.get("x-death")
    _count = _deaf_header[0].get("count")
    LOGGER.info(f"----Message received from dead letter queue----: {message.raw_message.routing_key} with count {_count}")
    if _count >= 3:
        LOGGER.info(f"Maximum retries reached for message: {message.raw_message.routing_key}")
        return
    await rmq_broker.publish(
        message.body,
        exchange=RabbitMQEvents.fetch_url.exchange,
        routing_key=RabbitMQEvents.fetch_url.routing_key,
        headers=message.headers,
    )
    LOGGER.info(f"---- Republished message to main queue ----: {RabbitMQEvents.fetch_url.routing_key}")


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
    await CONTAINER.crawling_service().fetch_info_from_url(message.url)
    LOGGER.info(f"----Message processed----: {message}")
