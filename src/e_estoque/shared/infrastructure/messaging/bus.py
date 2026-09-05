"""Adapter MessageBus → RabbitMQ: publish best-effort após o commit (NFR-REL-001).

Falha do broker NUNCA derruba a request — loga e segue (o .NET publicava de forma
síncrona fire-and-forget; aqui o contrato de wire é idêntico, a resiliência melhora).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from e_estoque.shared.domain.notifications import (
    ErrorNotification,
    LoginUserNotification,
    NotificationError,
)
from e_estoque.shared.infrastructure.messaging.rabbit import RabbitPublisher
from e_estoque.shared.infrastructure.messaging.wire import event_payload, routing_key

logger = logging.getLogger(__name__)


class DirectMessageBus:
    """Publica eventos de domínio e notificações; degrada silenciosamente sem broker."""

    def __init__(self, publisher: RabbitPublisher) -> None:
        self._publisher = publisher

    async def _send(self, payload_obj: Any, exchange: str, key: str) -> None:
        body = json.dumps(event_payload(payload_obj), ensure_ascii=False).encode()
        try:
            await self._publisher.publish_raw(body, exchange, key)
        except Exception as exc:  # noqa: BLE001 - broker indisponível não falha a request
            logger.warning("publish %s/%s falhou: %s", exchange, key, exc)

    async def publish(self, event: Any, exchange: str) -> None:
        await self._send(event, exchange, routing_key(event))

    async def publish_notification_error(
        self, event_name: str, description: str, exchange: str
    ) -> None:
        await self._send(
            NotificationError(event_name=event_name, description=description),
            exchange,
            "notification-error",
        )

    async def publish_error_notification(self, notification: ErrorNotification) -> None:
        await self._send(notification, "noticiation-service", "error-notification")

    async def publish_login_notification(self, notification: LoginUserNotification) -> None:
        await self._send(notification, "noticiation-service", "login-user-notification")
