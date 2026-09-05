"""Company: entidade, value object, eventos, critérios e porta de repositório."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID

from e_estoque.shared.domain.checks import (
    audit,
    length,
    required,
    when,
)
from e_estoque.shared.domain.entity import DomainEvent, Entity, new_id, utcnow
from e_estoque.shared.domain.search import SearchResult

EXCHANGE = "company-service"


# ---- Domain Events ----
@dataclass(frozen=True, slots=True)
class CompanyCreated(DomainEvent):
    id: UUID
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    company_address: "CompanyAddress"
    occurred_on: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class CompanyUpdated(DomainEvent):
    id: UUID
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    company_address: "CompanyAddress"
    occurred_on: datetime = field(default_factory=utcnow)


# ---- Value Object ----
@dataclass(frozen=True, slots=True)
class CompanyAddress:
    """Endereço da empresa (value object imutável; colunas `CompanyAddress_*` no PG)."""

    street: str
    number: str
    complement: str
    neighborhood: str
    district: str
    city: str
    country: str
    zip_code: str
    latitude: str
    longitude: str


# ---- Entity ----
class Company(Entity):
    __slots__ = (
        "name", "doc_id", "email", "description", "phone_number", "company_address",
    )

    def __init__(
        self,
        id: UUID,  # noqa: A002
        name: str,
        doc_id: str,
        email: str,
        description: str,
        phone_number: str,
        company_address: CompanyAddress,
        created_at: datetime,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
        is_deleted: bool = False,
    ) -> None:
        super().__init__(id, created_at, updated_at, deleted_at, is_deleted)
        self.name = name
        self.doc_id = doc_id
        self.email = email
        self.description = description
        self.phone_number = phone_number
        self.company_address = company_address

    @classmethod
    def create(
        cls,
        name: str,
        doc_id: str,
        email: str,
        description: str,
        phone_number: str,
        company_address: CompanyAddress,
    ) -> "Company":
        company = cls(
            new_id(), name, doc_id, email, description, phone_number,
            company_address, utcnow(),
        )
        company.register_event(
            CompanyCreated(
                company.id, name, doc_id, email, description, phone_number, company_address
            )
        )
        company.validate()
        return company

    @classmethod
    def rehydrate(
        cls,
        id: UUID,  # noqa: A002
        name: str,
        doc_id: str,
        email: str,
        description: str,
        phone_number: str,
        company_address: CompanyAddress,
        created_at: datetime,
        updated_at: datetime | None,
        deleted_at: datetime | None,
        is_deleted: bool,
    ) -> "Company":
        company = cls(
            id, name, doc_id, email, description, phone_number, company_address,
            created_at, updated_at, deleted_at, is_deleted,
        )
        company.validate()
        return company

    def update(
        self,
        name: str,
        doc_id: str,
        email: str,
        description: str,
        phone_number: str,
        company_address: CompanyAddress,
    ) -> None:
        self.name = name
        self.doc_id = doc_id
        self.email = email
        self.description = description
        self.phone_number = phone_number
        self.company_address = company_address
        self.touch(utcnow())
        self.register_event(
            CompanyUpdated(
                self.id, name, doc_id, email, description, phone_number, company_address
            )
        )
        self.validate()

    def validate(self) -> None:
        """CompanyValidation: mensagens/ordem do .NET (`{Prop} is required`)."""
        errors: list[str] = []
        audit(self.id, self.created_at, self.updated_at, self.deleted_at, errors)
        required(errors, self.name, "Name")
        length(errors, self.name, "Name", 3, 80)
        required(errors, self.doc_id, "DocId")
        length(errors, self.doc_id, "DocId", 3, 80)
        required(errors, self.email, "Email")
        length(errors, self.email, "Email", 3, 250)
        required(errors, self.description, "Description")
        length(errors, self.description, "Description", 3, 250)
        required(errors, self.phone_number, "PhoneNumber")
        length(errors, self.phone_number, "PhoneNumber", 3, 80)
        if self.company_address is None:
            required(errors, None, "CompanyAddress")
        else:
            address = self.company_address
            # Paridade: Longitude não possui regra no .NET.
            for prop, value in (
                ("Street", address.street),
                ("Number", address.number),
                ("Complement", address.complement),
                ("Neighborhood", address.neighborhood),
                ("District", address.district),
                ("City", address.city),
                ("Country", address.country),
                ("ZipCode", address.zip_code),
                ("Latitude", address.latitude),
            ):
                required(errors, value, prop)
                when(
                    value is not None and not 3 <= len(value) <= 80,
                    f"The {prop} need to have between 3 and 80 characters",
                    errors,
                )
        if errors:
            self.mark_invalid(errors)
        else:
            self.mark_valid()


# ---- Criteria / Port ----
@dataclass(frozen=True, slots=True)
class CompanyCriteria:
    id: UUID | None = None
    name: str | None = None
    doc_id: str | None = None
    email: str | None = None
    description: str | None = None
    phone_number: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    order: str | None = None
    page: int = 1
    size: int = 10


class CompanyRepository(Protocol):
    async def save(self, company: Company) -> None: ...

    async def find_by_id(self, company_id: UUID) -> Company | None: ...

    async def exists(self, company_id: UUID) -> bool: ...

    async def search(self, criteria: CompanyCriteria) -> SearchResult[Company]: ...

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Company]: ...

    async def delete_hard(self, company_id: UUID) -> None: ...
