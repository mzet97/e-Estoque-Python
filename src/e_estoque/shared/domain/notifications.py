"""Eventos de notificação publicados no broker (payloads do .NET)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from e_estoque.shared.domain.entity import DomainEvent, utcnow


@dataclass(frozen=True, slots=True)
class NotificationError(DomainEvent):
    """Falha de handler: {eventName, description, occurredOn} → exchange de notificações."""

    event_name: str
    description: str
    occurred_on: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class ErrorNotification:
    """Login inválido: {message, stackTrace} (sem occurredOn — paridade do .NET)."""

    message: str
    stack_trace: str = ""


@dataclass(frozen=True, slots=True)
class LoginUserNotification:
    """Login bem-sucedido: {username}."""

    username: str
