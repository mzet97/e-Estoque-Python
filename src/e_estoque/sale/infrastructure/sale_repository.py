"""Repositório SQLAlchemy de Sale (includes Customer/SaleProducts/Product; delete soft)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.sale.domain.sale import (
    EXCHANGE,
    PaymentType,
    Sale,
    SaleCriteria,
    SaleProduct,
    SaleRepository,
    SaleType,
)
from e_estoque.sale.infrastructure.models import (
    CustomerSummaryModel,
    SaleModel,
    SaleProductModel,
)
from e_estoque.shared.application.filtering import parse_gridify_filter
from e_estoque.shared.application.read_models import (
    AddressSummary,
    CategorySummary,
    CompanySummary,
    CustomerSummary,
    Detailed,
    ProductSummary,
)
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
    "idcustomer": FieldDef("id_customer", FieldType.UUID),
    "saledate": FieldDef("sale_date", FieldType.INSTANT),
    "createdat": FieldDef("created_at", FieldType.INSTANT),
    "updatedat": FieldDef("updated_at", FieldType.INSTANT),
    "deletedat": FieldDef("deleted_at", FieldType.INSTANT),
    "isdeleted": FieldDef("is_deleted", FieldType.BOOLEAN),
}

__all__ = [
    "EXCHANGE",
    "FILTER_FIELDS",
    "SqlSaleRepository",
    "SaleType",
    "PaymentType",
]


def _to_lines(model: SaleModel) -> list[SaleProduct]:
    return [
        SaleProduct(
            line.id, line.quantity, line.id_product, line.id_sale,
            line.created_at, line.updated_at, line.deleted_at, line.is_deleted,
        )
        for line in model.sale_products
    ]


def _to_domain(model: SaleModel) -> Sale:
    return Sale.rehydrate(
        model.id, model.quantity, model.total_price, model.total_tax,
        SaleType(model.sale_type), PaymentType(model.payment_type),
        model.delivery_date, model.sale_date, model.payment_date,
        model.id_customer, _to_lines(model),
        model.created_at, model.updated_at, model.deleted_at, model.is_deleted,
    )


def _address(address: CustomerSummaryModel | CompanySummaryModel) -> AddressSummary:
    return AddressSummary(
        street=address.address_street, number=address.address_number,
        complement=address.address_complement, neighborhood=address.address_neighborhood,
        district=address.address_district, city=address.address_city,
        country=address.address_country, zip_code=address.address_zip_code,
        latitude=address.address_latitude, longitude=address.address_longitude,
    )


def _customer_summary(model: CustomerSummaryModel | None) -> CustomerSummary | None:
    if model is None:
        return None
    return CustomerSummary(
        id=model.id, name=model.name, doc_id=model.doc_id, email=model.email,
        description=model.description, phone_number=model.phone_number,
        customer_address=_address(model),
        created_at=model.created_at, updated_at=model.updated_at, deleted_at=model.deleted_at,
    )


def _product_summary(model: Any) -> ProductSummary | None:
    if model is None:
        return None
    category: CategorySummary | None = None
    if model.category_rel is not None:
        category = CategorySummary(
            id=model.category_rel.id, name=model.category_rel.name,
            description=model.category_rel.description,
            short_description=model.category_rel.short_description,
            created_at=model.category_rel.created_at,
            updated_at=model.category_rel.updated_at,
            deleted_at=model.category_rel.deleted_at,
        )
    company: CompanySummary | None = None
    if model.company_rel is not None:
        company = CompanySummary(
            id=model.company_rel.id, name=model.company_rel.name,
            doc_id=model.company_rel.doc_id, email=model.company_rel.email,
            description=model.company_rel.description,
            phone_number=model.company_rel.phone_number,
            company_address=_address(model.company_rel),
            created_at=model.company_rel.created_at,
            updated_at=model.company_rel.updated_at,
            deleted_at=model.company_rel.deleted_at,
        )
    return ProductSummary(
        id=model.id, name=model.name, description=model.description,
        short_description=model.short_description, image=model.image,
        price=model.price, weight=model.weight, height=model.height,
        length=model.length, id_category=model.id_category, id_company=model.id_company,
        created_at=model.created_at, updated_at=model.updated_at, deleted_at=model.deleted_at,
        category=category, company=company,
    )


class SqlSaleRepository(SaleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, sale: Sale) -> None:
        model = await self._session.get(SaleModel, sale.id)
        if model is None:
            model = SaleModel(
                id=sale.id, quantity=sale.quantity, total_price=sale.total_price,
                total_tax=sale.total_tax, sale_type=int(sale.sale_type),
                payment_type=int(sale.payment_type), delivery_date=sale.delivery_date,
                sale_date=sale.sale_date, payment_date=sale.payment_date,
                id_customer=sale.id_customer, created_at=sale.created_at,
                updated_at=sale.updated_at, deleted_at=sale.deleted_at,
                is_deleted=sale.is_deleted,
            )
            model.sale_products = [self._line_model(line, sale.id) for line in sale.sale_products]
            self._session.add(model)
            return
        model.quantity = sale.quantity
        model.total_price = sale.total_price
        model.total_tax = sale.total_tax
        model.sale_type = int(sale.sale_type)
        model.payment_type = int(sale.payment_type)
        model.delivery_date = sale.delivery_date
        model.sale_date = sale.sale_date
        model.payment_date = sale.payment_date
        model.id_customer = sale.id_customer
        model.updated_at = sale.updated_at
        model.deleted_at = sale.deleted_at
        model.is_deleted = sale.is_deleted
        # Paridade do Sale.Update .NET: a coleção de linhas é substituída.
        # (No .NET o EF quebrava a associação; aqui as linhas são sincronizadas — BUG-FIX.)
        existing = list(model.sale_products)
        model.sale_products = []
        for line in existing:
            await self._session.delete(line)
        model.sale_products = [self._line_model(line, sale.id) for line in sale.sale_products]

    async def find_by_id(self, sale_id: UUID) -> Sale | None:
        model = await self._session.get(SaleModel, sale_id)
        return None if model is None else _to_domain(model)

    async def find_detailed_by_id(self, sale_id: UUID) -> Detailed[Sale] | None:
        model = await self._session.get(SaleModel, sale_id)
        if model is None:
            return None
        return Detailed(
            entity=_to_domain(model),
            customer=_customer_summary(model.customer_rel),
            products=[_product_summary(line.product_rel) for line in model.sale_products],
        )

    async def search(self, criteria: SaleCriteria) -> SearchResult[Detailed[Sale]]:
        stmt: Select[tuple[SaleModel]] = select(SaleModel)
        model = SaleModel
        if criteria.id is not None:
            stmt = stmt.where(model.id == criteria.id)
        if criteria.quantity is not None:
            stmt = stmt.where(model.quantity == criteria.quantity)
        if criteria.total_price is not None:
            stmt = stmt.where(model.total_price == criteria.total_price)
        if criteria.total_tax is not None:
            stmt = stmt.where(model.total_tax == criteria.total_tax)
        if criteria.sale_type:
            stmt = stmt.where(model.sale_type == int(SaleType.from_string(criteria.sale_type)))
        if criteria.payment_type:
            stmt = stmt.where(
                model.payment_type == int(PaymentType.from_string(criteria.payment_type))
            )
        if criteria.delivery_date is not None:
            stmt = stmt.where(model.delivery_date == criteria.delivery_date)
        if criteria.sale_date is not None:
            stmt = stmt.where(model.sale_date == criteria.sale_date)
        if criteria.payment_date is not None:
            stmt = stmt.where(model.payment_date == criteria.payment_date)
        if criteria.id_customer is not None:
            stmt = stmt.where(model.id_customer == criteria.id_customer)
        if criteria.id_product is not None:
            stmt = stmt.where(
                exists(
                    select(1).where(
                        SaleProductModel.id_sale == model.id,
                        SaleProductModel.id_product == criteria.id_product,
                    )
                )
            )
        if criteria.created_at is not None:
            stmt = stmt.where(model.created_at == criteria.created_at)
        if criteria.updated_at is not None:
            stmt = stmt.where(model.updated_at == criteria.updated_at)
        if criteria.deleted_at is not None:
            stmt = stmt.where(model.deleted_at == criteria.deleted_at)
        return await self._run_paged(stmt, criteria.page, criteria.size, criteria.order)

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Detailed[Sale]]:
        stmt: Select[tuple[SaleModel]] = select(SaleModel)
        where = build_filter(parse_gridify_filter(filter_text), SaleModel, FILTER_FIELDS)
        if where is not None:
            stmt = stmt.where(where)
        return await self._run_paged(stmt, page, size, order_text)

    async def disable(self, sale_id: UUID, now: datetime) -> bool:
        model = await self._session.get(SaleModel, sale_id)
        if model is None:
            return False
        model.is_deleted = True
        model.deleted_at = now
        return True

    async def _run_paged(
        self, stmt: Select[tuple[SaleModel]], page: int, size: int, order_text: str | None
    ) -> SearchResult[Detailed[Sale]]:
        total = await count_rows(self._session, stmt)
        stmt = stmt.order_by(*order_columns(order_text, SaleModel, FILTER_FIELDS))
        rows = await page_rows(self._session, stmt, page, size)
        models = [row[0] for row in rows]
        return SearchResult(
            data=[self._detailed(m) for m in models], row_count=total, page=page, size=size
        )

    def _detailed(self, model: SaleModel) -> Detailed[Sale]:
        return Detailed(
            entity=_to_domain(model),
            customer=_customer_summary(model.customer_rel),
            products=[_product_summary(line.product_rel) for line in model.sale_products],
        )

    @staticmethod
    def _line_model(line: SaleProduct, sale_id: UUID) -> SaleProductModel:
        line.id_sale = sale_id
        return SaleProductModel(
            id=line.id, quantity=line.quantity, id_product=line.id_product,
            id_sale=sale_id, created_at=line.created_at, updated_at=line.updated_at,
            deleted_at=line.deleted_at, is_deleted=line.is_deleted,
        )
