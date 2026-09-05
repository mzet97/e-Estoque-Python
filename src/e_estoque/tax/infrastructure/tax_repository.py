"""Repositório SQLAlchemy de Tax (include Category; delete = hard delete)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.shared.application.filtering import parse_gridify_filter
from e_estoque.shared.application.read_models import CategorySummary, Detailed
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.paging import count_rows, first_row, page_rows
from e_estoque.shared.infrastructure.sql_filtering import (
    FieldDef,
    FieldType,
    build_filter,
    order_columns,
)
from e_estoque.tax.domain.tax import Tax, TaxCriteria, TaxRepository
from e_estoque.tax.infrastructure.models import CategorySummaryModel, TaxModel

FILTER_FIELDS = {
    "id": FieldDef("id", FieldType.UUID),
    "name": FieldDef("name", FieldType.STRING),
    "description": FieldDef("description", FieldType.STRING),
    "percentage": FieldDef("percentage", FieldType.NUMBER),
    "idcategory": FieldDef("id_category", FieldType.UUID),
    "createdat": FieldDef("created_at", FieldType.INSTANT),
    "updatedat": FieldDef("updated_at", FieldType.INSTANT),
    "deletedat": FieldDef("deleted_at", FieldType.INSTANT),
    "isdeleted": FieldDef("is_deleted", FieldType.BOOLEAN),
}


def _to_domain(model: TaxModel) -> Tax:
    return Tax.rehydrate(
        model.id,
        model.name,
        model.description,
        model.percentage,
        model.id_category,
        model.created_at,
        model.updated_at,
        model.deleted_at,
        model.is_deleted,
    )


def _category_summary(model: CategorySummaryModel | None) -> CategorySummary | None:
    if model is None:
        return None
    return CategorySummary(
        id=model.id,
        name=model.name,
        description=model.description,
        short_description=model.short_description,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def _base_stmt() -> Select[tuple[TaxModel, CategorySummaryModel]]:
    return select(TaxModel, CategorySummaryModel).outerjoin(
        CategorySummaryModel, TaxModel.id_category == CategorySummaryModel.id
    )


class SqlTaxRepository(TaxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, tax: Tax) -> None:
        model = await self._session.get(TaxModel, tax.id)
        if model is None:
            self._session.add(
                TaxModel(
                    id=tax.id,
                    name=tax.name,
                    description=tax.description,
                    percentage=tax.percentage,
                    id_category=tax.id_category,
                    created_at=tax.created_at,
                    updated_at=tax.updated_at,
                    deleted_at=tax.deleted_at,
                    is_deleted=tax.is_deleted,
                )
            )
            return
        model.name = tax.name
        model.description = tax.description
        model.percentage = tax.percentage
        model.id_category = tax.id_category
        model.updated_at = tax.updated_at
        model.deleted_at = tax.deleted_at
        model.is_deleted = tax.is_deleted

    async def find_by_id(self, tax_id: UUID) -> Tax | None:
        model = await self._session.get(TaxModel, tax_id)
        return None if model is None else _to_domain(model)

    async def find_detailed_by_id(self, tax_id: UUID) -> Detailed[Tax] | None:
        stmt = _base_stmt().where(TaxModel.id == tax_id)
        row = await first_row(self._session, stmt)
        if row is None:
            return None
        tax_model, category = row
        return Detailed(entity=_to_domain(tax_model), category=_category_summary(category))

    async def search(self, criteria: TaxCriteria) -> SearchResult[Detailed[Tax]]:
        stmt = _base_stmt()
        model = TaxModel
        if criteria.id is not None:
            stmt = stmt.where(model.id == criteria.id)
        if criteria.name:
            stmt = stmt.where(model.name == criteria.name)
        if criteria.description:
            stmt = stmt.where(model.description == criteria.description)
        if criteria.percentage is not None and criteria.percentage != 0:
            stmt = stmt.where(model.percentage == criteria.percentage)
        if criteria.id_category is not None:
            stmt = stmt.where(model.id_category == criteria.id_category)
        if criteria.created_at is not None:
            stmt = stmt.where(model.created_at == criteria.created_at)
        if criteria.updated_at is not None:
            stmt = stmt.where(model.updated_at == criteria.updated_at)
        if criteria.deleted_at is not None:
            stmt = stmt.where(model.deleted_at == criteria.deleted_at)
        return await self._run_paged(stmt, criteria.page, criteria.size, criteria.order)

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Detailed[Tax]]:
        stmt = _base_stmt()
        where = build_filter(parse_gridify_filter(filter_text), TaxModel, FILTER_FIELDS)
        if where is not None:
            stmt = stmt.where(where)
        return await self._run_paged(stmt, page, size, order_text)

    async def delete_hard(self, tax_id: UUID) -> None:
        model = await self._session.get(TaxModel, tax_id)
        if model is not None:
            await self._session.delete(model)

    async def _run_paged(
        self,
        stmt: Select[tuple[TaxModel, CategorySummaryModel]],
        page: int,
        size: int,
        order_text: str | None,
    ) -> SearchResult[Detailed[Tax]]:
        total = await count_rows(self._session, stmt)
        stmt = stmt.order_by(*order_columns(order_text, TaxModel, FILTER_FIELDS))
        rows = await page_rows(self._session, stmt, page, size)
        data = [
            Detailed(entity=_to_domain(row[0]), category=_category_summary(row[1])) for row in rows
        ]
        return SearchResult(data=data, row_count=total, page=page, size=size)
