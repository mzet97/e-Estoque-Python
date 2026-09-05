"""Porta do barramento de mensagens (RabbitMQ no adapter; fake nos testes)."""

from __future__ import annotations

from typing import Any, Protocol

from e_estoque.shared.domain.notifications import ErrorNotification, LoginUserNotification

NOTIFICATION_EXCHANGE = "noticiation-service"  # typo do .NET preservado (wire parity)
NOTIFICATION_EXCHANGE_SALES = "notification-service"  # Sales handlers usam a grafia correta


class MessageBus(Protocol):
    """Publish fire-and-forget após a persistência (sem outbox — ADR-010)."""

    async def publish(self, event: Any, exchange: str) -> None: ...

    async def publish_notification_error(
        self, event_name: str, description: str, exchange: str
    ) -> None: ...

    async def publish_error_notification(self, notification: ErrorNotification) -> None: ...

    async def publish_login_notification(self, notification: LoginUserNotification) -> None: ...
