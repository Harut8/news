from typing import Optional

import retry_async
from faststream.rabbit import RabbitBroker

from src.core.utils.base_dtos import BaseDto
from src.core.utils.types import UUID_STR, get_random_uuid_as_str


class RabbitMQPublisher:
    def __init__(self, broker_adapter: RabbitBroker, logger):
        self._broker_adapter: RabbitBroker = broker_adapter
        self._logger = logger

    @retry_async.retry(is_async=True, tries=3, delay=2, backoff=1, max_delay=5)
    async def publish(
        self,
        message: BaseDto | dict,
        queue_name: str = "",
        exchange_name: Optional[str] = None,
        routing_key: Optional[str] = None,
        correlation_id: UUID_STR | None = None,
        message_id: UUID_STR | None = None,
        headers: dict | None = None,
    ):
        try:
            message_id = message_id or get_random_uuid_as_str()
            correlation_id = correlation_id or get_random_uuid_as_str()
            _headers = {"rbs2-content-type": "application/json"}
            if headers:
                _headers.update(headers)
            headers = _headers
            await self._broker_adapter.publish(
                message,
                queue_name,
                exchange_name,
                routing_key=routing_key,
                correlation_id=correlation_id,
                message_id=message_id,
                persist=True,
                headers=headers,
            )
            self._logger.info("######## PUBLISHED TO RMQ ########")
            self._logger.info(
                f"Message {message} published \n"
                f"with id {message_id} \n"
                f"to queue {queue_name} by exchange {exchange_name} \n"
                f"with routing_key {routing_key} \n"
                f"with correlation_id {correlation_id} \n"
                f"with headers {headers}"
            )
        except Exception as e:
            self._logger.error(f"Failed to publish message to RMQ: {e}")
