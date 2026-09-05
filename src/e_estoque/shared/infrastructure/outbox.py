"""Transactional Outbox: modelo, publisher (porta) e dispatcher worker (ADR-010)."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from sqlalchemy import String, select, update
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from e_estoque.shared.domain.events import DomainEvent

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5


class OutboxBase(DeclarativeBase):
    pass


class OutboxEventModel(OutboxBase):
    """Tabela outbox_events (V2) — gravada na MESMA transação do agregado."""

    __tablename__ = "outbox_events"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    event_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(String(100))
    exchange: Mapped[str] = mapped_column(String(100))
    routing_key: Mapped[str] = mapped_column(String(200))
    payload: Mapped[str] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    attempts: Mapped[int] = mapped_column(default=0)
    correlation_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(timezone=True)
    processed_at: Mapped[datetime | None] = mapped_column(timezone=True, nullable=True)


@dataclass(frozen=True, slots=True)
class NotificationPayload:
    """NotificationError do .NET: {message, details}."""

    message: str
    details: str


class OutboxRepository(Protocol):
    async def add(self, event: OutboxEventModel) -> None: ...
    async def pending(self, limit: int = 50) -> list[OutboxEventModel]: ...
    async def save(self, event: OutboxEventModel) -> None: ...


class OutboxEventPublisher:
    """Implementa as portas de publicação: grava na transação corrente."""

    NOTIFICATION_EXCHANGE = "notification-service"

    def __init__(self, session: Any) -> None:
        self._session = session

    async def publish(self, event: DomainEvent, exchange: str) -> None:
        from e_estoque.shared.infrastructure.messaging.wire import (
            routing_key,
            serialize_event,
        )

        row = OutboxEventModel(
            id=uuid4(),
            event_id=uuid4(),
            event_type=type(event).__name__,
            exchange=exchange,
            routing_key=routing_key(event),
            payload=json.loads(serialize_event(event)),
            status="PENDING",
            occurred_at=datetime.now(UTC),
        )
        self._session.add(row)
        await self._session.flush()

    async def publish_error(self, message: str, details: str) -> None:
        payload = NotificationPayload(message=message, details=details)
        row = OutboxEventModel(
            id=uuid4(),
            event_id=uuid4(),
            event_type="NotificationError",
            exchange=self.NOTIFICATION_EXCHANGE,
            routing_key="notification-error",
            payload=json.loads(json.dumps(dataclasses_asdict(payload))),
            status="PENDING",
            occurred_at=datetime.now(UTC),
        )
        self._session.add(row)
        await self._session.flush()


def dataclasses_asdict(value: Any) -> dict[str, Any]:
    import dataclasses

    return dataclasses.asdict(value)


class OutboxDispatcher:
    """Worker: publica pendências no RabbitMQ com retry; FAILED = dead-letter."""

    def __init__(self, session_factory: Any, publish: Any) -> None:
        self._session_factory = session_factory
        self._publish = publish

    async def dispatch_pending(self) -> int:
        count = 0
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(OutboxEventModel)
                    .where(OutboxEventModel.status == "PENDING")
                    .order_by(OutboxEventModel.occurred_at)
                    .limit(50)
                )
            ).scalars()
            for row in rows:
                row.attempts += 1
                try:
                    await self._publish(
                        row.payload, row.exchange, row.routing_key
                    )
                    row.status = "PUBLISHED"
                    row.processed_at = datetime.now(UTC)
                except Exception as exc:  # noqa: BLE001 - worker não pode cair
                    if row.attempts >= MAX_ATTEMPTS:
                        row.status = "FAILED"
                        row.processed_at = datetime.now(UTC)
                        logger.error("outbox %s falhou definitivamente: %s", row.event_id, exc)
                    else:
                        logger.warning("outbox %s tentativa %d falhou: %s", row.event_id, row.attempts, exc)
                await session.execute(
                    update(OutboxEventModel)
                    .where(OutboxEventModel.id == row.id)
                    .values(
                        status=row.status,
                        attempts=row.attempts,
                        processed_at=row.processed_at,
                    )
                )
                count += 1
            await session.commit()
        return count

    async def run_forever(self, interval_seconds: float = 5.0) -> None:
        while True:
            try:
                await self.dispatch_pending()
            except Exception as exc:  # noqa: BLE001
                logger.warning("outbox dispatch falhou: %s", exc)
            await asyncio.sleep(interval_seconds)
