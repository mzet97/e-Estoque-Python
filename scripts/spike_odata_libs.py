"""Spike: avalia `odata-query` (gorilla) contra os models reais (sqlite in-memory).

Somente expressões ORM parametrizadas — strings de teste são literais fixas.
"""

import asyncio
import sys
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, "src")
from e_estoque.product.infrastructure.models import CategoryModel, ProductBase

CASES = [
    "name eq 'Bebidas'",
    "contains(description,'sucos')",
    "startswith(name,'Be')",
    "name eq 'X' or name eq 'Y'",
    "createdAt gt 2026-01-01T00:00:00Z",
    "id eq 11111111-1111-1111-1111-111111111111",
    "id eq '11111111-1111-1111-1111-111111111111'",
    "isDeleted eq true",
    "Name eq 'Bebidas'",  # PascalCase (contrato OData .NET) — resolve?
    "unknownField eq 1",  # campo fora do modelo — erro seguro?
]


async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(ProductBase.metadata.create_all)
    maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with maker() as session:
        session.add(
            CategoryModel(
                id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
                name="Bebidas",
                description="Refrigerantes e sucos",
                short_description="Geladas",
                created_at=datetime(2026, 5, 1, tzinfo=UTC),
                updated_at=None,
                deleted_at=None,
                is_deleted=False,
            )
        )
        await session.commit()

        from odata_query.sqlalchemy import apply_odata_query

        for case in CASES:
            try:
                stmt = apply_odata_query(select(CategoryModel), case)
                rows = (await session.scalars(stmt)).all()
                print(f"OK   {case!r} -> {len(rows)} row(s)")
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL {case!r} -> {type(exc).__name__}: {str(exc)[:160]}")

    await engine.dispose()


asyncio.run(main())
