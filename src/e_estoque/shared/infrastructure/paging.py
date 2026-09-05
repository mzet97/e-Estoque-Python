"""Paginação compartilhada dos repositórios (count pós-filtro + offset/limit).

Valores de página/tamanho entram como parâmetros vinculados do SQLAlchemy —
nunca são interpolados em texto SQL.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func
from sqlalchemy.ext.asyncio import AsyncSession


async def count_rows(session: AsyncSession, stmt: Select[Any]) -> int:
    """Total de linhas do statement (após filtros), sem ordenação."""
    count_stmt = stmt.with_only_columns(func.count()).order_by(None)
    result = await session.scalar(count_stmt)
    return int(result or 0)


async def page_rows(session: AsyncSession, stmt: Select[Any], page: int, size: int) -> list[Any]:
    """Aplica offset/limit 1-based e devolve as linhas da página."""
    paged = stmt.offset((page - 1) * size).limit(size)
    return list((await session.execute(paged)).all())


async def page_scalars(session: AsyncSession, stmt: Select[Any], page: int, size: int) -> list[Any]:
    """Como `page_rows`, para selects de entidade única (devolve entidades)."""
    paged = stmt.offset((page - 1) * size).limit(size)
    return list((await session.scalars(paged)).all())


async def one_or_none(session: AsyncSession, stmt: Select[Any]) -> Any:
    """Primeira coluna da primeira linha (a entidade do select) ou None."""
    return await session.scalar(stmt)


async def first_row(session: AsyncSession, stmt: Select[Any]) -> Any:
    """Primeira Row completa (para selects de múltiplas entidades) ou None."""
    return (await session.execute(stmt)).first()
