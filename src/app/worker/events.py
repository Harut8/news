from enum import Enum


class RabbitMQEvents(Enum):
    fetch_url = ("news.direct", "news.crawler.fetch_url", "crawler.fetch_url")

    def __init__(self, exchange, queue, routing_key):
        self._exchange = exchange
        self._queue = queue
        self._routing_key = routing_key

    @property
    def exchange(self):
        return self._exchange

    @property
    def queue(self):
        return self._queue

    @property
    def routing_key(self):
        return self._routing_key

    @property
    def queue_dead_letter(self):
        return f"{self.queue}_dead_letter"

    @property
    def exchange_dead_letter(self):
        return f"{self.exchange}_dead_letter"

    @property
    def routing_key_dead_letter(self):
        return f"{self.routing_key}_dead_letter"