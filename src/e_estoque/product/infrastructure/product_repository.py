"""Repositório SQLAlchemy de Product (joins = includes do .NET, sem N+1).

Todas as consultas usam expressões ORM parametrizadas com whitelist de campos —
o SQL é gerado pelo SQLAlchemy com bindings; a execução passa pelos helpers de
`shared.infrastructure.paging` (contagem pós-filtro, paginação 1-based).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from e_estoque.product.domain.product import Product, ProductCriteria, ProductRepository
from e_estoque.product.infrastructure.models import (
    CategoryModel,
    CompanySummaryModel,
    ProductModel,
)
from e_estoque.shared.application.filtering import parse_gridify_filter
from e_estoque.shared.application.read_models import (
    AddressSummary,
    CategorySummary,
    CompanySummary,
    Detailed,
)
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.paging import count_rows, one_or_none, page_rows
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
    "price": FieldDef("price", FieldType.NUMBER),
    "weight": FieldDef("weight", FieldType.NUMBER),
    "height": FieldDef("height", FieldType.NUMBER),
    "length": FieldDef("length", FieldType.NUMBER),
    "image": FieldDef("image", FieldType.STRING),
    "idcategory": FieldDef("id_category", FieldType.UUID),
    "idcompany": FieldDef("id_company", FieldType.UUID),
    "createdat": FieldDef("created_at", FieldType.INSTANT),
    "updatedat": FieldDef("updated_at", FieldType.INSTANT),
    "deletedat": FieldDef("deleted_at", FieldType.INSTANT),
    "isdeleted": FieldDef("is_deleted", FieldType.BOOLEAN),
}


def _to_domain(model: ProductModel) -> Product:
    return Product.rehydrate(
        model.id, model.name, model.description, model.short_description,
        model.price, model.weight, model.height, model.length, model.image,
        model.id_category, model.id_company,
        model.created_at, model.updated_at, model.deleted_at, model.is_deleted,
    )


def _category_summary(model: CategoryModel | None) -> CategorySummary | None:
    if model is None:
        return None
    return CategorySummary(
        id=model.id, name=model.name, description=model.description,
        short_description=model.short_description,
        created_at=model.created_at, updated_at=model.updated_at, deleted_at=model.deleted_at,
    )


def _company_summary(model: CompanySummaryModel | None) -> CompanySummary | None:
    if model is None:
        return None
    return CompanySummary(
        id=model.id, name=model.name, doc_id=model.doc_id, email=model.email,
        description=model.description, phone_number=model.phone_number,
        company_address=AddressSummary(
            street=model.address_street, number=model.address_number,
            complement=model.address_complement, neighborhood=model.address_neighborhood,
            district=model.address_district, city=model.address_city,
            country=model.address_country, zip_code=model.address_zip_code,
            latitude=model.address_latitude, longitude=model.address_longitude,
        ),
        created_at=model.created_at, updated_at=model.updated_at, deleted_at=model.deleted_at,
    )


def _to_detailed(model: ProductModel) -> Detailed[Product]:
    return Detailed(
        entity=_to_domain(model),
        category=_category_summary(model.category_rel),
        company=_company_summary(model.company_rel),
    )


def _detailed_stmt() -> Select[tuple[ProductModel]]:
    return select(ProductModel).options(
        selectinload(ProductModel.category_rel),
        selectinload(ProductModel.company_rel),
    )


class SqlProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, product: Product) -> None:
        model = await self._session.get(ProductModel, product.id)
        if model is None:
            self._session.add(
                ProductModel(
                    id=product.id, name=product.name, description=product.description,
                    short_description=product.short_description, price=product.price,
                    weight=product.weight, height=product.height, length=product.length,
                    image=product.image, id_category=product.id_category,
                    id_company=product.id_company, created_at=product.created_at,
                    updated_at=product.updated_at, deleted_at=product.deleted_at,
                    is_deleted=product.is_deleted,
                )
            )
            return
        model.name = product.name
        model.description = product.description
        model.short_description = product.short_description
        model.price = product.price
        model.weight = product.weight
        model.height = product.height
        model.length = product.length
        model.image = product.image
        model.id_category = product.id_category
        model.id_company = product.id_company
        model.updated_at = product.updated_at
        model.deleted_at = product.deleted_at
        model.is_deleted = product.is_deleted

    async def find_by_id(self, product_id: UUID) -> Product | None:
        model = await self._session.get(ProductModel, product_id)
        return None if model is None else _to_domain(model)

    async def exists(self, product_id: UUID) -> bool:
        stmt = select(ProductModel.id).where(ProductModel.id == product_id)
        return (await self._session.scalar(stmt)) is not None

    async def find_detailed_by_id(self, product_id: UUID) -> Detailed[Product] | None:
        stmt = _detailed_stmt().where(ProductModel.id == product_id)
        model = await one_or_none(self._session, stmt)
        return None if model is None else _to_detailed(model)

    async def search(self, criteria: ProductCriteria) -> SearchResult[Detailed[Product]]:
        stmt = _detailed_stmt()
        model = ProductModel
        if criteria.id is not None:
            stmt = stmt.where(model.id == criteria.id)
        if criteria.name:
            stmt = stmt.where(model.name == criteria.name)
        if criteria.description:
            stmt = stmt.where(model.description == criteria.description)
        if criteria.short_description:
            stmt = stmt.where(model.short_description == criteria.short_description)
        if criteria.price is not None:
            stmt = stmt.where(model.price == criteria.price)
        if criteria.weight is not None:
            stmt = stmt.where(model.weight == criteria.weight)
        if criteria.height is not None:
            stmt = stmt.where(model.height == criteria.height)
        if criteria.length is not None:
            stmt = stmt.where(model.length == criteria.length)
        if criteria.id_category is not None:
            stmt = stmt.where(model.id_category == criteria.id_category)
        if criteria.id_company is not None:
            stmt = stmt.where(model.id_company == criteria.id_company)
        if criteria.created_at is not None:
            stmt = stmt.where(model.created_at == criteria.created_at)
        if criteria.updated_at is not None:
            stmt = stmt.where(model.updated_at == criteria.updated_at)
        if criteria.deleted_at is not None:
            stmt = stmt.where(model.deleted_at == criteria.deleted_at)
        total = await count_rows(self._session, stmt)
        stmt = stmt.order_by(*order_columns(criteria.order, model, FILTER_FIELDS))
        models = [row[0] for row in await page_rows(self._session, stmt, criteria.page, criteria.size)]
        return SearchResult(
            data=[_to_detailed(m) for m in models],
            row_count=total,
            page=criteria.page,
            size=criteria.size,
        )

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Detailed[Product]]:
        stmt = _detailed_stmt()
        where = build_filter(parse_gridify_filter(filter_text), ProductModel, FILTER_FIELDS)
        if where is not None:
            stmt = stmt.where(where)
        total = await count_rows(self._session, stmt)
        stmt = stmt.order_by(*order_columns(order_text, ProductModel, FILTER_FIELDS))
        models = [row[0] for row in await page_rows(self._session, stmt, page, size)]
        return SearchResult(data=[_to_detailed(m) for m in models], row_count=total, page=page, size=size)

    async def delete_hard(self, product_id: UUID) -> None:
        model = await self._session.get(ProductModel, product_id)
        if model is not None:
            await self._session.delete(model)
