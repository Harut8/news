from faststream.rabbit import RabbitQueue, RabbitExchange

from src.app.worker.dto import FetchUrlDto
from src.app.worker.events import RabbitMQEvents
from src.core.conf.settings import SETTINGS
from src.core.di import DependencyContainer
from src.core.utils.api.logger import LOGGER

CONTAINER = DependencyContainer()
CONTAINER.config.from_dict(SETTINGS.model_dump())
rmq_broker = CONTAINER.rmq_broker()
consumer_app = CONTAINER.faststream_app()


@rmq_broker.subscriber(
    RabbitQueue(RabbitMQEvents.fetch_url.queue, durable=True, routing_key=RabbitMQEvents.fetch_url.routing_key),
    RabbitExchange(RabbitMQEvents.fetch_url.exchange, durable=True),
)
async def fetch_info_from_url(message: FetchUrlDto):
    LOGGER.info(f"----Message received----: {message}")
    await CONTAINER.crawling_service().fetch_info_from_url(message.url)
