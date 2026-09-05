"""Porta Unit of Work (application não conhece a implementação SQLAlchemy)."""

from __future__ import annotations

from typing import Protocol, Self


class UnitOfWork(Protocol):
    """Transação por unidade de trabalho; rollback automático ao sair com erro."""

    async def __aenter__(self) -> Self: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
