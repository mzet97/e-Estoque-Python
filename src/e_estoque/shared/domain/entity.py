"""Base de entidades e eventos de domínio (Python puro, sem frameworks)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


def utcnow() -> datetime:
    """Agora em UTC (timezone consciente — nunca naive)."""
    return datetime.now(UTC)


def new_id() -> UUID:
    return uuid4()


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Marker base de eventos de domínio (payload = campos do registro)."""


class Entity:
    """Base de entidades: identidade UUID, auditoria, soft delete e eventos.

    Entidades acumulam erros de validação em validate() sem lançar exceção —
    o handler de aplicação decide o que fazer (paridade com o .NET).
    """

    __slots__ = (
        "id",
        "created_at",
        "updated_at",
        "deleted_at",
        "is_deleted",
        "_events",
        "_errors",
        "_valid",
    )

    def __init__(
        self,
        id: UUID,  # noqa: A002 - identidade do .NET é "Id"
        created_at: datetime,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
        is_deleted: bool = False,
    ) -> None:
        self.id = id
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at
        self.is_deleted = is_deleted
        self._events: list[Any] = []
        self._errors: list[str] = []
        self._valid = False

    def register_event(self, event: Any) -> None:
        self._events.append(event)

    def pull_events(self) -> list[Any]:
        events, self._events = self._events, []
        return events

    @property
    def errors(self) -> list[str]:
        return self._errors

    def mark_valid(self) -> None:
        self._errors = []
        self._valid = True

    def mark_invalid(self, errors: list[str]) -> None:
        self._errors = list(errors)
        self._valid = False

    @property
    def is_valid(self) -> bool:
        return self._valid

    @property
    def joined_errors(self) -> str:
        """Mensagens unidas por vírgula, como no contrato .NET."""
        return ",".join(self._errors)

    def touch(self, now: datetime) -> None:
        self.updated_at = now

    def disable(self, now: datetime) -> None:
        """Soft delete: mantém a linha com is_deleted=True e deleted_at."""
        self.is_deleted = True
        self.deleted_at = now

    def activate(self) -> None:
        self.is_deleted = False
        self.deleted_at = None
