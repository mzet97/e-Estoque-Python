"""Repositório SQLAlchemy de Category (delete = hard delete, parity .NET)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.product.domain.category import (
    Category,
    CategoryCriteria,
    CategoryRepository,
)
from e_estoque.product.infrastructure.models import CategoryModel
from e_estoque.shared.application.filtering import parse_gridify_filter
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.sql_filtering import build_filter

ORDER_FIELDS = {
    "name": "name",
    "description": "description",
    "shortdescription": "short_description",
    "createdat": "created_at",
    "updatedat": "updated_at",
    "deletedat": "deleted_at",
}


def _to_domain(m: CategoryModel) -> Category:
    return Category.rehydrate(
        m.id,
        m.name,
        m.description,
        m.short_description,
        m.created_at,
        m.updated_at,
        m.deleted_at,
        m.is_deleted,
    )


class SqlCategoryRepository(CategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, category: Category) -> None:
        model = await self._session.get(CategoryModel, category.id)
        if model is None:
            model = CategoryModel(
                id=category.id,
                name=category.name,
                description=category.description,
                short_description=category.short_description,
                created_at=category.created_at,
                updated_at=category.updated_at,
                deleted_at=category.deleted_at,
                is_deleted=category.is_deleted,
            )
            self._session.add(model)
            return
        model.name = category.name
        model.description = category.description
        model.short_description = category.short_description
        model.updated_at = category.updated_at
        model.deleted_at = category.deleted_at
        model.is_deleted = category.is_deleted

    async def find_by_id(self, category_id: uuid.UUID) -> Category | None:
        model = await self._session.get(CategoryModel, category_id)
        if model is None:
            return None
        return _to_domain(model)

    async def search(self, criteria: CategoryCriteria) -> SearchResult[Category]:
        model = CategoryModel
        stmt = select(model)
        if criteria.name:
            stmt = stmt.filter_by(name=criteria.name)
        if criteria.description:
            stmt = stmt.filter_by(description=criteria.description)
        if criteria.short_description:
            stmt = stmt.filter_by(short_description=criteria.short_description)
        if criteria.id:
            stmt = stmt.filter_by(id=criteria.id)
        if criteria.created_at:
            stmt = stmt.filter_by(created_at=criteria.created_at)
        if criteria.updated_at:
            stmt = stmt.filter_by(updated_at=criteria.updated_at)
        if criteria.deleted_at:
            stmt = stmt.filter_by(deleted_at=criteria.deleted_at)
        order_name = ORDER_FIELDS.get((criteria.order or "").lower(), "id")
        stmt = stmt.order_by(asc(getattr(model, order_name)))
        stmt = stmt.offset((criteria.page - 1) * criteria.size).limit(criteria.size)
        rows = (await self._session.execute(stmt)).scalars().all()
        total = (
            await self._session.execute(select(func.count()).select_from(model))
        ).scalar_one()
        data = [_to_domain(r) for r in rows]
        return SearchResult(data=data, row_count=total, page=criteria.page, size=criteria.size)

    async def search_gridify(
        self,
        filter_text: str | None,
        order_text: str | None,
        page: int,
        size: int,
    ) -> SearchResult[Category]:
        model = CategoryModel
        stmt = select(model)
        node = parse_gridify_filter(filter_text)
        if node is not None:
            where = build_filter(node, model, ORDER_FIELDS)
            if where is not None:
                stmt = stmt.where(where)
        order_name = ORDER_FIELDS.get((order_text or "").lower(), "id")
        stmt = stmt.order_by(asc(getattr(model, order_name)))
        stmt = stmt.offset((page - 1) * size).limit(size)
        rows = (await self._session.execute(stmt)).scalars().all()
        total = (
            await self._session.execute(select(func.count()).select_from(model))
        ).scalar_one()
        data = [_to_domain(r) for r in rows]
        return SearchResult(data=data, row_count=total, page=page, size=size)

    async def delete_hard(self, category_id: uuid.UUID) -> None:
        model = await self._session.get(CategoryModel, category_id)
        if model is not None:
            await self._session.delete(model)
