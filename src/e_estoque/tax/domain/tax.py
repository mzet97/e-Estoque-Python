"""Tax: entidade, eventos, critérios e porta de repositório."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

from e_estoque.shared.application.read_models import Detailed
from e_estoque.shared.domain.checks import (
    audit,
    inclusive_range,
    length,
    provided,
    provided_number,
)
from e_estoque.shared.domain.entity import DomainEvent, Entity, utcnow
from e_estoque.shared.domain.search import SearchResult

EXCHANGE = "tax-service"


# ---- Domain Events ----
@dataclass(frozen=True, slots=True)
class TaxCreated(DomainEvent):
    id: UUID
    name: str
    description: str
    percentage: Decimal
    id_category: UUID
    occurred_on: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class TaxUpdated(DomainEvent):
    id: UUID
    name: str
    description: str
    percentage: Decimal
    id_category: UUID
    occurred_on: datetime = field(default_factory=utcnow)


# ---- Entity ----
class Tax(Entity):
    __slots__ = ("name", "description", "percentage", "id_category")

    def __init__(
        self,
        id: UUID,  # noqa: A002
        name: str,
        description: str,
        percentage: Decimal,
        id_category: UUID,
        created_at: datetime,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
        is_deleted: bool = False,
    ) -> None:
        super().__init__(id, created_at, updated_at, deleted_at, is_deleted)
        self.name = name
        self.description = description
        self.percentage = percentage
        self.id_category = id_category

    @classmethod
    def create(cls, name: str, description: str, percentage: Decimal, id_category: UUID) -> Tax:
        tax = cls(uuid4(), name, description, percentage, id_category, utcnow())
        tax.register_event(TaxCreated(tax.id, name, description, percentage, id_category))
        tax.validate()
        return tax

    @classmethod
    def rehydrate(
        cls,
        id: UUID,  # noqa: A002
        name: str,
        description: str,
        percentage: Decimal,
        id_category: UUID,
        created_at: datetime,
        updated_at: datetime | None,
        deleted_at: datetime | None,
        is_deleted: bool,
    ) -> Tax:
        tax = cls(
            id,
            name,
            description,
            percentage,
            id_category,
            created_at,
            updated_at,
            deleted_at,
            is_deleted,
        )
        tax.validate()
        return tax

    def update(self, name: str, description: str, percentage: Decimal, id_category: UUID) -> None:
        self.name = name
        self.description = description
        self.percentage = percentage
        self.id_category = id_category
        self.touch(utcnow())
        self.register_event(TaxUpdated(self.id, name, description, percentage, id_category))
        self.validate()

    def validate(self) -> None:
        errors: list[str] = []
        audit(self.id, self.created_at, self.updated_at, self.deleted_at, errors)
        provided(errors, self.name, "Name")
        length(errors, self.name, "Name", 3, 80)
        provided(errors, self.description, "Description")
        length(errors, self.description, "Description", 3, 250)
        provided_number(errors, self.percentage, "Percentage")
        inclusive_range(errors, self.percentage, "Percentage", 0, 100)
        if errors:
            self.mark_invalid(errors)
        else:
            self.mark_valid()


# ---- Criteria / Port ----
@dataclass(frozen=True, slots=True)
class TaxCriteria:
    id: UUID | None = None
    name: str | None = None
    description: str | None = None
    percentage: Decimal | None = None
    id_category: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    order: str | None = None
    page: int = 1
    size: int = 10


class CategoryReader(Protocol):
    """Verificação de existência de Category (referencial do Tax)."""

    async def exists(self, category_id: UUID) -> bool: ...


class TaxRepository(Protocol):
    async def save(self, tax: Tax) -> None: ...

    async def find_by_id(self, tax_id: UUID) -> Tax | None: ...

    async def find_detailed_by_id(self, tax_id: UUID) -> Detailed[Tax] | None: ...

    async def search(self, criteria: TaxCriteria) -> SearchResult[Detailed[Tax]]: ...

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Detailed[Tax]]: ...

    async def delete_hard(self, tax_id: UUID) -> None: ...
