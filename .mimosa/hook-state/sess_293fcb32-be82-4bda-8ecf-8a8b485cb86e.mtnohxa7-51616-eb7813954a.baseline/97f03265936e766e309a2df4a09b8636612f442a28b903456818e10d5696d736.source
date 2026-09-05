"""Publisher RabbitMQ (aio-pika): exchanges topic duráveis, JSON camelCase."""

from __future__ import annotations

import json
import logging
from typing import Any

import aio_pika

logger = logging.getLogger(__name__)

KNOWN_EXCHANGES = (
    "product-service",
    "category-service",
    "company-service",
    "customer-service",
    "inventory-service",
    "sale-service",
    "tax-service",
    "notification-service",
)


class RabbitPublisher:
    """Publica payloads já serializados; declara a exchange topic no envio."""

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self._url = f"amqp://{username}:{password}@{host}:{port}/"
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        channel = await self._connection.channel()
        for name in KNOWN_EXCHANGES:
            await channel.declare_exchange(name, aio_pika.ExchangeType.TOPIC, durable=True)

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def publish(self, payload: dict[str, Any], exchange: str, routing_key: str) -> None:
        if self._connection is None:
            await self.connect()
        assert self._connection is not None
        channel = await self._connection.channel()
        exchange_obj = await channel.declare_exchange(
            exchange, aio_pika.ExchangeType.TOPIC, durable=True
        )
        message = aio_pika.Message(body=json.dumps(payload, ensure_ascii=False).encode())
        await exchange_obj.publish(message, routing_key=routing_key)
