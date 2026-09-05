"""Repositório SQLAlchemy de Inventory (includes Product+Category+Company do .NET)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.inventory.domain.inventory import (
    Inventory,
    InventoryCriteria,
    InventoryRepository,
)
from e_estoque.inventory.infrastructure.models import (
    CategorySummaryModel,
    CompanySummaryModel,
    InventoryModel,
    ProductSummaryModel,
)
from e_estoque.shared.application.filtering import parse_gridify_filter
from e_estoque.shared.application.read_models import (
    AddressSummary,
    CategorySummary,
    CompanySummary,
    Detailed,
    ProductSummary,
)
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.paging import count_rows, first_row, page_rows
from e_estoque.shared.infrastructure.sql_filtering import (
    FieldDef,
    FieldType,
    build_filter,
    order_columns,
)

FILTER_FIELDS = {
    "id": FieldDef("id", FieldType.UUID),
    "idproduct": FieldDef("id_product", FieldType.UUID),
    "quantity": FieldDef("quantity", FieldType.NUMBER),
    "minquantity": FieldDef("quantity", FieldType.NUMBER),  # campo decorativo do .NET
    "maxquantity": FieldDef("quantity", FieldType.NUMBER),  # campo decorativo do .NET
    "dateorder": FieldDef("date_order", FieldType.STRING),
    "createdat": FieldDef("created_at", FieldType.INSTANT),
    "updatedat": FieldDef("updated_at", FieldType.INSTANT),
    "deletedat": FieldDef("deleted_at", FieldType.INSTANT),
    "isdeleted": FieldDef("is_deleted", FieldType.BOOLEAN),
}

# Paridade: DateOrder é varchar(80) no banco; domínio trata datetime (A-01).
DATE_ORDER_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _parse_date_order(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


def _to_domain(model: InventoryModel) -> Inventory:
    return Inventory.rehydrate(
        model.id,
        model.quantity,
        _parse_date_order(model.date_order),
        model.id_product,
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


def _company_summary(model: CompanySummaryModel | None) -> CompanySummary | None:
    if model is None:
        return None
    return CompanySummary(
        id=model.id,
        name=model.name,
        doc_id=model.doc_id,
        email=model.email,
        description=model.description,
        phone_number=model.phone_number,
        company_address=AddressSummary(
            street=model.address_street,
            number=model.address_number,
            complement=model.address_complement,
            neighborhood=model.address_neighborhood,
            district=model.address_district,
            city=model.address_city,
            country=model.address_country,
            zip_code=model.address_zip_code,
            latitude=model.address_latitude,
            longitude=model.address_longitude,
        ),
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def _product_summary(
    product: ProductSummaryModel | None,
    category: CategorySummaryModel | None,
    company: CompanySummaryModel | None,
) -> ProductSummary | None:
    if product is None:
        return None
    return ProductSummary(
        id=product.id,
        name=product.name,
        description=product.description,
        short_description=product.short_description,
        image=product.image,
        price=product.price,
        weight=product.weight,
        height=product.height,
        length=product.length,
        id_category=product.id_category,
        id_company=product.id_company,
        created_at=product.created_at,
        updated_at=product.updated_at,
        deleted_at=product.deleted_at,
        category=_category_summary(category),
        company=_company_summary(company),
    )


class SqlInventoryRepository(InventoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, inventory: Inventory) -> None:
        model = await self._session.get(InventoryModel, inventory.id)
        date_order = inventory.date_order.strftime(DATE_ORDER_FORMAT)
        if model is None:
            self._session.add(
                InventoryModel(
                    id=inventory.id,
                    quantity=inventory.quantity,
                    date_order=date_order,
                    id_product=inventory.id_product,
                    created_at=inventory.created_at,
                    updated_at=inventory.updated_at,
                    deleted_at=inventory.deleted_at,
                    is_deleted=inventory.is_deleted,
                )
            )
            return
        model.quantity = inventory.quantity
        model.date_order = date_order
        model.id_product = inventory.id_product
        model.updated_at = inventory.updated_at
        model.deleted_at = inventory.deleted_at
        model.is_deleted = inventory.is_deleted

    async def find_by_id(self, inventory_id: UUID) -> Inventory | None:
        model = await self._session.get(InventoryModel, inventory_id)
        return None if model is None else _to_domain(model)

    async def find_detailed_by_id(self, inventory_id: UUID) -> Detailed[Inventory] | None:
        stmt = self._base_stmt().where(InventoryModel.id == inventory_id)
        row = await first_row(self._session, stmt)
        if row is None:
            return None
        inventory_model, product, category, company = row
        return Detailed(
            entity=_to_domain(inventory_model),
            product=_product_summary(product, category, company),
        )

    async def search(self, criteria: InventoryCriteria) -> SearchResult[Detailed[Inventory]]:
        stmt = self._base_stmt()
        model = InventoryModel
        if criteria.id is not None:
            stmt = stmt.where(model.id == criteria.id)
        if criteria.quantity is not None:
            stmt = stmt.where(model.quantity == criteria.quantity)
        if criteria.date_order is not None:
            stmt = stmt.where(model.date_order == criteria.date_order.isoformat())
        if criteria.id_product is not None:
            stmt = stmt.where(model.id_product == criteria.id_product)
        if criteria.created_at is not None:
            stmt = stmt.where(model.created_at == criteria.created_at)
        if criteria.updated_at is not None:
            stmt = stmt.where(model.updated_at == criteria.updated_at)
        if criteria.deleted_at is not None:
            stmt = stmt.where(model.deleted_at == criteria.deleted_at)
        return await self._run_paged(stmt, criteria.page, criteria.size, criteria.order)

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Detailed[Inventory]]:
        stmt = self._base_stmt()
        where = build_filter(parse_gridify_filter(filter_text), InventoryModel, FILTER_FIELDS)
        if where is not None:
            stmt = stmt.where(where)
        return await self._run_paged(stmt, page, size, order_text)

    async def delete_hard(self, inventory_id: UUID) -> None:
        model = await self._session.get(InventoryModel, inventory_id)
        if model is not None:
            await self._session.delete(model)

    # ---- helpers ----
    def _base_stmt(self) -> Select[tuple[Any, ...]]:
        """Inventory + includes do .NET: Product, Product.Category, Product.Company."""
        return (
            select(
                InventoryModel,
                ProductSummaryModel,
                CategorySummaryModel,
                CompanySummaryModel,
            )
            .outerjoin(ProductSummaryModel, InventoryModel.id_product == ProductSummaryModel.id)
            .outerjoin(
                CategorySummaryModel, ProductSummaryModel.id_category == CategorySummaryModel.id
            )
            .outerjoin(
                CompanySummaryModel, ProductSummaryModel.id_company == CompanySummaryModel.id
            )
        )

    async def _run_paged(
        self, stmt: Select[tuple[Any, ...]], page: int, size: int, order_text: str | None
    ) -> SearchResult[Detailed[Inventory]]:
        total = await count_rows(self._session, stmt)
        stmt = stmt.order_by(*order_columns(order_text, InventoryModel, FILTER_FIELDS))
        rows = await page_rows(self._session, stmt, page, size)
        data = [
            Detailed(
                entity=_to_domain(row[0]),
                product=_product_summary(row[1], row[2], row[3]),
            )
            for row in rows
        ]
        return SearchResult(data=data, row_count=total, page=page, size=size)
