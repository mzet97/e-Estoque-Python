"""Repositório SQLAlchemy de Company (sem includes no .NET; delete = hard delete)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select

from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.company.domain.company import Company, CompanyAddress, CompanyCriteria
from e_estoque.company.infrastructure.models import CompanyModel
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
    "docid": FieldDef("doc_id", FieldType.STRING),
    "cnpj": FieldDef("doc_id", FieldType.STRING),
    "email": FieldDef("email", FieldType.STRING),
    "description": FieldDef("description", FieldType.STRING),
    "phonenumber": FieldDef("phone_number", FieldType.STRING),
    "phone": FieldDef("phone_number", FieldType.STRING),
    "createdat": FieldDef("created_at", FieldType.INSTANT),
    "updatedat": FieldDef("updated_at", FieldType.INSTANT),
    "deletedat": FieldDef("deleted_at", FieldType.INSTANT),
    "isdeleted": FieldDef("is_deleted", FieldType.BOOLEAN),
}


def _to_domain(model: CompanyModel) -> Company:
    return Company.rehydrate(
        model.id, model.name, model.doc_id, model.email, model.description,
        model.phone_number,
        CompanyAddress(
            street=model.address_street, number=model.address_number,
            complement=model.address_complement, neighborhood=model.address_neighborhood,
            district=model.address_district, city=model.address_city,
            country=model.address_country, zip_code=model.address_zip_code,
            latitude=model.address_latitude, longitude=model.address_longitude,
        ),
        model.created_at, model.updated_at, model.deleted_at, model.is_deleted,
    )


class SqlCompanyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, company: Company) -> None:
        model = await self._session.get(CompanyModel, company.id)
        if model is None:
            self._session.add(self._to_model(company))
            return
        self._apply(model, company)

    async def find_by_id(self, company_id: UUID) -> Company | None:
        model = await self._session.get(CompanyModel, company_id)
        return None if model is None else _to_domain(model)

    async def exists(self, company_id: UUID) -> bool:
        stmt = select(CompanyModel.id).where(CompanyModel.id == company_id)
        found = await self._session.scalar(stmt)
        return found is not None

    async def count_all(self) -> int:
        return int(
            await self._session.scalar(select(func.count()).select_from(CompanyModel)) or 0
        )

    async def search(self, criteria: CompanyCriteria) -> SearchResult[Company]:
        model = CompanyModel
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
        rows = await page_rows(self._session, stmt, criteria.page, criteria.size)
        return SearchResult(
            data=[_to_domain(row) for row in rows],
            row_count=total, page=criteria.page, size=criteria.size,
        )

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Company]:
        model = CompanyModel
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

    async def delete_hard(self, company_id: UUID) -> None:
        model = await self._session.get(CompanyModel, company_id)
        if model is not None:
            await self._session.delete(model)

    @staticmethod
    def _to_model(company: Company) -> CompanyModel:
        return CompanyModel(
            id=company.id, name=company.name, doc_id=company.doc_id, email=company.email,
            description=company.description, phone_number=company.phone_number,
            address_street=company.company_address.street,
            address_number=company.company_address.number,
            address_complement=company.company_address.complement,
            address_neighborhood=company.company_address.neighborhood,
            address_district=company.company_address.district,
            address_city=company.company_address.city,
            address_country=company.company_address.country,
            address_zip_code=company.company_address.zip_code,
            address_latitude=company.company_address.latitude,
            address_longitude=company.company_address.longitude,
            created_at=company.created_at, updated_at=company.updated_at,
            deleted_at=company.deleted_at, is_deleted=company.is_deleted,
        )

    @staticmethod
    def _apply(model: CompanyModel, company: Company) -> None:
        model.name = company.name
        model.doc_id = company.doc_id
        model.email = company.email
        model.description = company.description
        model.phone_number = company.phone_number
        model.address_street = company.company_address.street
        model.address_number = company.company_address.number
        model.address_complement = company.company_address.complement
        model.address_neighborhood = company.company_address.neighborhood
        model.address_district = company.company_address.district
        model.address_city = company.company_address.city
        model.address_country = company.company_address.country
        model.address_zip_code = company.company_address.zip_code
        model.address_latitude = company.company_address.latitude
        model.address_longitude = company.company_address.longitude
        model.updated_at = company.updated_at
        model.deleted_at = company.deleted_at
        model.is_deleted = company.is_deleted
