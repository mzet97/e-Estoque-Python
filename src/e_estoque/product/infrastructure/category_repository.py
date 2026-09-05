"""Repositório SQLAlchemy de Category (delete = hard delete, paridade .NET).

Paridades preservadas:
- Search: filtros de igualdade exata; `short_description` filtra a coluna Description
  (bug do SearchCategoryQueryHandler .NET preservado — MIGRATION-DIFFERENCES #10).
- Count pós-filtro (comportamento do Repository<T> base .NET).
- Filtros/ordenação sempre via expressões ORM parametrizadas (whitelist de campos).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.product.domain.category import Category, CategoryCriteria, CategoryRepository
from e_estoque.product.infrastructure.models import CategoryModel
from e_estoque.shared.application.filtering import parse_gridify_filter
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.paging import count_rows, page_rows
from e_estoque.shared.infrastructure.sql_filtering import (
    FieldDef,
    FieldType,
    build_filter,
    order_columns,
)

FILTER_FIELDS = {
    "id": FieldDef("id", FieldType.UUID),
    "name": FieldDef("name", FieldType.STRING),
    "description": FieldDef("description", FieldType.STRING),
    "shortdescription": FieldDef("short_description", FieldType.STRING),
    "createdat": FieldDef("created_at", FieldType.INSTANT),
    "updatedat": FieldDef("updated_at", FieldType.INSTANT),
    "deletedat": FieldDef("deleted_at", FieldType.INSTANT),
    "isdeleted": FieldDef("is_deleted", FieldType.BOOLEAN),
}


def _to_domain(model: CategoryModel) -> Category:
    return Category.rehydrate(
        model.id,
        model.name,
        model.description,
        model.short_description,
        model.created_at,
        model.updated_at,
        model.deleted_at,
        model.is_deleted,
    )


class SqlCategoryRepository(CategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, category: Category) -> None:
        model = await self._session.get(CategoryModel, category.id)
        if model is None:
            self._session.add(
                CategoryModel(
                    id=category.id,
                    name=category.name,
                    description=category.description,
                    short_description=category.short_description,
                    created_at=category.created_at,
                    updated_at=category.updated_at,
                    deleted_at=category.deleted_at,
                    is_deleted=category.is_deleted,
                )
            )
            return
        model.name = category.name
        model.description = category.description
        model.short_description = category.short_description
        model.updated_at = category.updated_at
        model.deleted_at = category.deleted_at
        model.is_deleted = category.is_deleted

    async def find_by_id(self, category_id: UUID) -> Category | None:
        model = await self._session.get(CategoryModel, category_id)
        return None if model is None else _to_domain(model)

    async def exists(self, category_id: UUID) -> bool:
        stmt = select(CategoryModel.id).where(CategoryModel.id == category_id)
        return (await self._session.scalar(stmt)) is not None

    async def search(self, criteria: CategoryCriteria) -> SearchResult[Category]:
        model = CategoryModel
        stmt = select(model)
        if criteria.id is not None:
            stmt = stmt.where(model.id == criteria.id)
        if criteria.name:
            stmt = stmt.where(model.name == criteria.name)
        if criteria.description:
            stmt = stmt.where(model.description == criteria.description)
        # Paridade do bug .NET: ShortDescription do filtro aplica na coluna Description.
        if criteria.short_description:
            stmt = stmt.where(model.description == criteria.short_description)
        if criteria.created_at is not None:
            stmt = stmt.where(model.created_at == criteria.created_at)
        if criteria.updated_at is not None:
            stmt = stmt.where(model.updated_at == criteria.updated_at)
        if criteria.deleted_at is not None:
            stmt = stmt.where(model.deleted_at == criteria.deleted_at)

        total = await count_rows(self._session, stmt)
        # Order do .NET é sempre ascendente; default Id para paginação determinística.
        stmt = stmt.order_by(*order_columns(criteria.order, model, FILTER_FIELDS))
        rows = await page_rows(self._session, stmt, criteria.page, criteria.size)
        return SearchResult(
            data=[_to_domain(row) for row in rows],
            row_count=total,
            page=criteria.page,
            size=criteria.size,
        )

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Category]:
        model = CategoryModel
        stmt = select(model)
        where = build_filter(parse_gridify_filter(filter_text), model, FILTER_FIELDS)
        if where is not None:
            stmt = stmt.where(where)
        total = await count_rows(self._session, stmt)
        stmt = stmt.order_by(*order_columns(order_text, model, FILTER_FIELDS))
        rows = await page_rows(self._session, stmt, page, size)
        return SearchResult(
            data=[_to_domain(row) for row in rows], row_count=total, page=page, size=size
        )

    async def delete_hard(self, category_id: UUID) -> None:
        model = await self._session.get(CategoryModel, category_id)
        if model is not None:
            await self._session.delete(model)
