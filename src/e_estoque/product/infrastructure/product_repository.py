"""Repositório SQLAlchemy de Product (joins = includes do .NET)."""

from __future__ import annotations

import uuid

from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.product.domain.product import (
    Product,
    ProductCriteria,
    ProductRepository,
    ProductViewCategory,
    ProductViewCompany,
    ProductViewData,
)
from e_estoque.product.infrastructure.gridify_columns import (
    product_order,
    product_where,
)
from e_estoque.product.infrastructure.models import (
    CategoryModel,
    CompanySummaryModel,
    ProductModel,
)
from e_estoque.shared.application.filtering import parse_gridify_filter
from e_estoque.shared.domain.search import SearchResult


def _to_domain(m: ProductModel) -> Product:
    return Product.rehydrate(
        m.id, m.name, m.description, m.short_description, m.price, m.weight,
        m.height, m.length, m.image, m.id_category, m.id_company,
        m.created_at, m.updated_at, m.deleted_at, m.is_deleted,
    )


def _to_view(
    p: ProductModel,
    c: CategoryModel | None,
    co: CompanySummaryModel | None,
) -> ProductViewData:
    category = None
    if c is not None:
        category = ProductViewCategory(
            id=c.id, name=c.name, description=c.description,
            short_description=c.short_description,
            created_at=c.created_at, updated_at=c.updated_at, deleted_at=c.deleted_at,
        )
    company = None
    if co is not None:
        company = ProductViewCompany(
            id=co.id, name=co.name, doc_id=co.doc_id, email=co.email,
            description=co.description, phone_number=co.phone_number,
            company_address=ProductViewCompany.Address(
                street=co.address_street, number=co.address_number,
                complement=co.address_complement, neighborhood=co.address_neighborhood,
                district=co.address_district, city=co.address_city,
                country=co.address_country, zip_code=co.address_zip_code,
                latitude=co.address_latitude, longitude=co.address_longitude,
            ),
            created_at=co.created_at, updated_at=co.updated_at, deleted_at=co.deleted_at,
        )
    return ProductViewData(product=_to_domain(p), category=category, company=company)


class SqlProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, product: Product) -> None:
        model = await self._session.get(ProductModel, product.id)
        if model is None:
            model = ProductModel(
                id=product.id, name=product.name, description=product.description,
                short_description=product.short_description, price=product.price,
                weight=product.weight, height=product.height, length=product.length,
                image=product.image, id_category=product.id_category,
                id_company=product.id_company, created_at=product.created_at,
                updated_at=product.updated_at, deleted_at=product.deleted_at,
                is_deleted=product.is_deleted,
            )
            self._session.add(model)
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

    async def find_by_id(self, product_id: uuid.UUID) -> Product | None:
        model = await self._session.get(ProductModel, product_id)
        if model is None:
            return None
        return _to_domain(model)

    async def find_detailed_by_id(self, product_id: uuid.UUID) -> ProductViewData | None:
        stmt = (
            select(ProductModel, CategoryModel, CompanySummaryModel)
            .join(CategoryModel, ProductModel.id_category == CategoryModel.id)
            .join(CompanySummaryModel, ProductModel.id_company == CompanySummaryModel.id)
            .where(ProductModel.id == product_id)
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            return None
        return _to_view(row[0], row[1], row[2])

    async def search(self, criteria: ProductCriteria) -> SearchResult[ProductViewData]:
        model = ProductModel
        stmt = select(model)
        if criteria.name:
            stmt = stmt.where(model.name == criteria.name)
        if criteria.description:
            stmt = stmt.where(model.description == criteria.description)
        if criteria.short_description:
            stmt = stmt.where(model.short_description == criteria.short_description)
        if criteria.price:
            stmt = stmt.where(model.price == criteria.price)
        if criteria.weight:
            stmt = stmt.where(model.weight == criteria.weight)
        if criteria.height:
            stmt = stmt.where(model.height == criteria.height)
        if criteria.length:
            stmt = stmt.where(model.length == criteria.length)
        if criteria.id_category:
            stmt = stmt.where(model.id_category == criteria.id_category)
        if criteria.id_company:
            stmt = stmt.where(model.id_company == criteria.id_company)
        if criteria.id:
            stmt = stmt.where(model.id == criteria.id)
        if criteria.created_at:
            stmt = stmt.where(model.created_at == criteria.created_at)
        if criteria.updated_at:
            stmt = stmt.where(model.updated_at == criteria.updated_at)
        if criteria.deleted_at:
            stmt = stmt.where(model.deleted_at == criteria.deleted_at)
        stmt = stmt.order_by(asc(model.id))
        stmt = stmt.offset((criteria.page - 1) * criteria.size).limit(criteria.size)
        rows = (await self._session.execute(stmt)).scalars().all()
        total = (await self._session.execute(select(func.count()).select_from(model))).scalar_one()
        data: list[ProductViewData] = []
        for r in rows:
            data.append(
                _to_view(
                    r,
                    await self._session.get(CategoryModel, r.id_category),
                    await self._session.get(CompanySummaryModel, r.id_company),
                )
            )
        return SearchResult(data=data, row_count=total, page=criteria.page, size=criteria.size)

    async def search_gridify(
        self,
        filter_text: str | None,
        order_text: str | None,
        page: int,
        size: int,
    ) -> SearchResult[ProductViewData]:
        stmt = select(ProductModel, CategoryModel, CompanySummaryModel)
        stmt = stmt.join(CategoryModel, ProductModel.id_category == CategoryModel.id)
        stmt = stmt.join(CompanySummaryModel, ProductModel.id_company == CompanySummaryModel.id)
        where = product_where(parse_gridify_filter(filter_text))
        if where is not None:
            stmt = stmt.where(where)
        order_cols = product_order(order_text)
        if order_cols:
            stmt = stmt.order_by(*order_cols)
        stmt = stmt.offset((page - 1) * size).limit(size)
        rows = (await self._session.execute(stmt)).all()
        total = (await self._session.execute(select(func.count()).select_from(ProductModel))).scalar_one()
        data = [_to_view(r[0], r[1], r[2]) for r in rows]
        return SearchResult(data=data, row_count=total, page=page, size=size)

    async def delete_hard(self, product_id: uuid.UUID) -> None:
        model = await self._session.get(ProductModel, product_id)
        if model is not None:
            await self._session.delete(model)
