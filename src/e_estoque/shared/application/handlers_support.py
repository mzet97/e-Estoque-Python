"""Suporte aos handlers de aplicação (dança comum: validar/notificar/levantar/publicar)."""

from __future__ import annotations

from typing import Any

from e_estoque.shared.application.message_bus import MessageBus
from e_estoque.shared.domain.entity import Entity
from e_estoque.shared.domain.errors import NotFoundError, ValidationError


async def ensure_valid(
    entity: Entity, bus: MessageBus, event_name: str, exchange: str
) -> None:
    """Entidade inválida → NotificationError no broker + ValidationError (HTTP 400)."""
    if not entity.is_valid:
        errors = entity.joined_errors
        await bus.publish_notification_error(event_name, errors, exchange)
        raise ValidationError(errors)


async def ensure_found(
    entity: Any,
    bus: MessageBus,
    notification: str,
    raise_message: str,
    exchange: str,
) -> None:
    """Entidade ausente → NotificationError no broker + NotFoundError (HTTP 404)."""
    if entity is None:
        await bus.publish_notification_error(notification, notification, exchange)
        raise NotFoundError(raise_message)


async def publish_events(entity: Entity, bus: MessageBus, exchange: str) -> None:
    """Publica os eventos acumulados no aggregate (após o commit)."""
    for event in entity.pull_events():
        await bus.publish(event, exchange)
