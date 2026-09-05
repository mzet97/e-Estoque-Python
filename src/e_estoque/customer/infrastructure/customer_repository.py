"""Repositório SQLAlchemy de Customer (delete = soft `DisableAsync`, paridade .NET)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.customer.domain.customer import Customer, CustomerAddress, CustomerCriteria
from e_estoque.customer.infrastructure.models import CustomerModel
from e_estoque.shared.application.filtering import parse_gridify_filter
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.paging import count_rows, page_scalars
from e_estoque.shared.infrastructure.sql_filtering import (
    FieldDef,
    FieldType,
    build_filter,
    order_columns,
)

FILTER_FIELDS = {
    "id": FieldDef("id", FieldType.UUID),
    "name": FieldDef("name", FieldType.STRING),
    "docid": FieldDef("doc_id", FieldType.STRING),
    "cpf": FieldDef("doc_id", FieldType.STRING),
    "email": FieldDef("email", FieldType.STRING),
    "description": FieldDef("description", FieldType.STRING),
    "phonenumber": FieldDef("phone_number", FieldType.STRING),
    "phone": FieldDef("phone_number", FieldType.STRING),
    "createdat": FieldDef("created_at", FieldType.INSTANT),
    "updatedat": FieldDef("updated_at", FieldType.INSTANT),
    "deletedat": FieldDef("deleted_at", FieldType.INSTANT),
    "isdeleted": FieldDef("is_deleted", FieldType.BOOLEAN),
}


def _to_domain(model: CustomerModel) -> Customer:
    return Customer.rehydrate(
        model.id,
        model.name,
        model.doc_id,
        model.email,
        model.description,
        model.phone_number,
        CustomerAddress(
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
        model.created_at,
        model.updated_at,
        model.deleted_at,
        model.is_deleted,
    )


class SqlCustomerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, customer: Customer) -> None:
        model = await self._session.get(CustomerModel, customer.id)
        if model is None:
            self._session.add(self._to_model(customer))
            return
        self._apply(model, customer)

    async def find_by_id(self, customer_id: UUID) -> Customer | None:
        model = await self._session.get(CustomerModel, customer_id)
        return None if model is None else _to_domain(model)

    async def exists(self, customer_id: UUID) -> bool:
        stmt = select(CustomerModel.id).where(CustomerModel.id == customer_id)
        found = await self._session.scalar(stmt)
        return found is not None

    async def search(self, criteria: CustomerCriteria) -> SearchResult[Customer]:
        model = CustomerModel
        stmt = select(model)
        if criteria.id is not None:
            stmt = stmt.where(model.id == criteria.id)
        for value, column in (
            (criteria.name, model.name),
            (criteria.doc_id, model.doc_id),
            (criteria.email, model.email),
            (criteria.description, model.description),
            (criteria.phone_number, model.phone_number),
        ):
            if value:
                stmt = stmt.where(column == value)
        if criteria.created_at is not None:
            stmt = stmt.where(model.created_at == criteria.created_at)
        if criteria.updated_at is not None:
            stmt = stmt.where(model.updated_at == criteria.updated_at)
        if criteria.deleted_at is not None:
            stmt = stmt.where(model.deleted_at == criteria.deleted_at)
        total = await count_rows(self._session, stmt)
        stmt = stmt.order_by(*order_columns(criteria.order, model, FILTER_FIELDS))
        rows = await page_scalars(self._session, stmt, criteria.page, criteria.size)
        return SearchResult(
            data=[_to_domain(row) for row in rows],
            row_count=total,
            page=criteria.page,
            size=criteria.size,
        )

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Customer]:
        model = CustomerModel
        stmt = select(model)
        where = build_filter(parse_gridify_filter(filter_text), model, FILTER_FIELDS)
        if where is not None:
            stmt = stmt.where(where)
        total = await count_rows(self._session, stmt)
        stmt = stmt.order_by(*order_columns(order_text, model, FILTER_FIELDS))
        rows = await page_scalars(self._session, stmt, page, size)
        return SearchResult(
            data=[_to_domain(row) for row in rows], row_count=total, page=page, size=size
        )

    async def disable(self, customer_id: UUID, now: datetime) -> bool:
        """Delete do .NET: DisableAsync (soft) — seta IsDeleted/DeletedAt."""
        model = await self._session.get(CustomerModel, customer_id)
        if model is None:
            return False
        model.is_deleted = True
        model.deleted_at = now
        return True

    @staticmethod
    def _to_model(customer: Customer) -> CustomerModel:
        return CustomerModel(
            id=customer.id,
            name=customer.name,
            doc_id=customer.doc_id,
            email=customer.email,
            description=customer.description,
            phone_number=customer.phone_number,
            address_street=customer.customer_address.street,
            address_number=customer.customer_address.number,
            address_complement=customer.customer_address.complement,
            address_neighborhood=customer.customer_address.neighborhood,
            address_district=customer.customer_address.district,
            address_city=customer.customer_address.city,
            address_country=customer.customer_address.country,
            address_zip_code=customer.customer_address.zip_code,
            address_latitude=customer.customer_address.latitude,
            address_longitude=customer.customer_address.longitude,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            deleted_at=customer.deleted_at,
            is_deleted=customer.is_deleted,
        )

    @staticmethod
    def _apply(model: CustomerModel, customer: Customer) -> None:
        model.name = customer.name
        model.doc_id = customer.doc_id
        model.email = customer.email
        model.description = customer.description
        model.phone_number = customer.phone_number
        model.address_street = customer.customer_address.street
        model.address_number = customer.customer_address.number
        model.address_complement = customer.customer_address.complement
        model.address_neighborhood = customer.customer_address.neighborhood
        model.address_district = customer.customer_address.district
        model.address_city = customer.customer_address.city
        model.address_country = customer.customer_address.country
        model.address_zip_code = customer.customer_address.zip_code
        model.address_latitude = customer.customer_address.latitude
        model.address_longitude = customer.customer_address.longitude
        model.updated_at = customer.updated_at
        model.deleted_at = customer.deleted_at
        model.is_deleted = customer.is_deleted
