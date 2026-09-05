"""Health checks: /health (paridade), /health/live e /health/ready."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.shared.infrastructure.db import open_session

router = APIRouter()


@router.get("/health")
async def health() -> Response:
    """Paridade .NET: `GET /health` → 200 "Healthy"."""
    return Response(content="Healthy", media_type="text/plain")


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready")
async def ready(session: Annotated[AsyncSession, Depends(open_session)]) -> object:
    """Readiness avalia a dependência essencial (PostgreSQL)."""
    try:
        await session.scalar(select(1))
    except Exception:  # noqa: BLE001 - readiness reporta 503, não derruba
        return Response(
            content='{"status":"unready"}',
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )
    return {"status": "ready"}
