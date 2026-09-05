"""Category: entidade, eventos, critérios e porta de repositório."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from typing import Protocol

from e_estoque.shared.domain.checks import audit, length, provided
from e_estoque.shared.domain.entity import DomainEvent, Entity, new_id, utcnow
from e_estoque.shared.domain.search import SearchResult

EXCHANGE = "category-service"


# ---- Domain Events (payload = wire format .NET) ----
@dataclass(frozen=True, slots=True)
class CategoryCreated(DomainEvent):
    id: UUID
    name: str
    description: str
    short_description: str
    occurred_on: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class CategoryUpdated(DomainEvent):
    id: UUID
    name: str
    description: str
    short_description: str
    occurred_on: datetime = field(default_factory=utcnow)


# ---- Entity ----
class Category(Entity):
    __slots__ = ("name", "description", "short_description")

    def __init__(
        self,
        id: UUID,  # noqa: A002 - identidade do .NET é "Id"
        name: str,
        description: str,
        short_description: str,
        created_at: datetime,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
        is_deleted: bool = False,
    ) -> None:
        super().__init__(id, created_at, updated_at, deleted_at, is_deleted)
        self.name = name
        self.description = description
        self.short_description = short_description

    @classmethod
    def create(cls, name: str, description: str, short_description: str) -> "Category":
        category = cls(new_id(), name, description, short_description, utcnow())
        category.register_event(
            CategoryCreated(category.id, name, description, short_description)
        )
        category.validate()
        return category

    @classmethod
    def rehydrate(
        cls,
        id: UUID,  # noqa: A002
        name: str,
        description: str,
        short_description: str,
        created_at: datetime,
        updated_at: datetime | None,
        deleted_at: datetime | None,
        is_deleted: bool,
    ) -> "Category":
        category = cls(
            id, name, description, short_description, created_at, updated_at, deleted_at, is_deleted
        )
        category.validate()
        return category

    def update(self, name: str, description: str, short_description: str) -> None:
        self.name = name
        self.description = description
        self.short_description = short_description
        self.touch(utcnow())
        self.register_event(CategoryUpdated(self.id, name, description, short_description))
        self.validate()

    def validate(self) -> None:
        errors: list[str] = []
        audit(self.id, self.created_at, self.updated_at, self.deleted_at, errors)
        provided(errors, self.name, "Name")
        length(errors, self.name, "Name", 3, 80)
        provided(errors, self.short_description, "ShortDescription")
        length(errors, self.short_description, "ShortDescription", 3, 500)
        provided(errors, self.description, "Description")
        length(errors, self.description, "Description", 3, 5000)
        if errors:
            self.mark_invalid(errors)
        else:
            self.mark_valid()


# ---- Criteria / Port ----
@dataclass(frozen=True, slots=True)
class CategoryCriteria:
    """Filtros de igualdade exata do SearchCategoryQuery (.NET)."""

    id: UUID | None = None
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    order: str | None = None
    page: int = 1
    size: int = 10


class CategoryRepository(Protocol):
    async def save(self, category: Category) -> None: ...

    async def find_by_id(self, category_id: UUID) -> Category | None: ...

    async def search(self, criteria: CategoryCriteria) -> SearchResult[Category]: ...

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Category]: ...

    async def delete_hard(self, category_id: UUID) -> None: ...
