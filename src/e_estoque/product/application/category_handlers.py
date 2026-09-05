"""Handlers CQRS de Category (Create/Update/Delete/GetById/Search/Gridify)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Union
from uuid import UUID

from e_estoque.product.domain.category import Category, CategoryCriteria, CategoryRepository
from e_estoque.shared.application.handlers_support import (
    ensure_found,
    ensure_valid,
    publish_events,
)
from e_estoque.shared.application.message_bus import NOTIFICATION_EXCHANGE, MessageBus
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.db import UnitOfWork

EXCHANGE = "category-service"


@dataclass(frozen=True, slots=True)
class CreateCategoryCommand:
    name: str
    description: str
    short_description: str


@dataclass(frozen=True, slots=True)
class UpdateCategoryCommand:
    id: UUID
    name: str
    description: str
    short_description: str


@dataclass(frozen=True, slots=True)
class DeleteCategoryCommand:
    id: UUID


@dataclass(frozen=True, slots=True)
class SearchCategoryQuery:
    name: str = ""
    description: str = ""
    short_description: str = ""
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    order: Optional[str] = None
    page_index: int = 1
    page_size: int = 10


@dataclass(frozen=True, slots=True)
class GridifyCategoryQuery:
    filter: Optional[str] = None
    order_by: Optional[str] = None
    page: int = 1
    page_size: int = 10


class CreateCategoryHandler:
    def __init__(
        self, repository: CategoryRepository, uow: UnitOfWork, bus: MessageBus
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: CreateCategoryCommand) -> UUID:
        category = Category.create(
            command.name, command.description, command.short_description
        )
        await ensure_valid(category, self._bus, "Validate Category has error", NOTIFICATION_EXCHANGE)
        await self._repository.save(category)
        await self._uow.commit()
        await publish_events(category, self._bus, EXCHANGE)
        return category.id


class UpdateCategoryHandler:
    def __init__(
        self, repository: CategoryRepository, uow: UnitOfWork, bus: MessageBus
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: UpdateCategoryCommand) -> UUID:
        category = await self._repository.find_by_id(command.id)
        await ensure_found(
            category, self._bus, "Update Category has error", "Find Error", NOTIFICATION_EXCHANGE
        )
        assert category is not None  # garantido por ensure_found
        category.update(command.name, command.description, command.short_description)
        await ensure_valid(category, self._bus, "Validate Category has error", NOTIFICATION_EXCHANGE)
        await self._repository.save(category)
        await self._uow.commit()
        await publish_events(category, self._bus, EXCHANGE)
        return category.id


class DeleteCategoryHandler:
    def __init__(
        self, repository: CategoryRepository, uow: UnitOfWork, bus: MessageBus
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: DeleteCategoryCommand) -> None:
        category = await self._repository.find_by_id(command.id)
        await ensure_found(
            category, self._bus, "Delete Category has error", "Delete Error", NOTIFICATION_EXCHANGE
        )
        assert category is not None  # garantido por ensure_found
        await self._repository.delete_hard(category.id)
        await self._uow.commit()


class GetByIdCategoryHandler:
    def __init__(self, repository: CategoryRepository, bus: MessageBus) -> None:
        self._repository = repository
        self._bus = bus

    async def handle(self, category_id: UUID) -> Category:
        category = await self._repository.find_by_id(category_id)
        await ensure_found(
            category, self._bus, "Not found Category", "Not found", NOTIFICATION_EXCHANGE
        )
        assert category is not None  # garantido por ensure_found
        return category


class SearchCategoryHandler:
    def __init__(self, repository: CategoryRepository) -> None:
        self._repository = repository

    async def handle(self, query: SearchCategoryQuery) -> SearchResult[Category]:
        criteria = CategoryCriteria(
            name=query.name,
            description=query.description,
            short_description=query.short_description,
            id=query.id,
            created_at=query.created_at,
            updated_at=query.updated_at,
            deleted_at=query.deleted_at,
            order=query.order,
            page=query.page_index,
            size=query.page_size,
        )
        return await self._repository.search(criteria)


class GridifyCategoryHandler:
    def __init__(self, repository: CategoryRepository) -> None:
        self._repository = repository

    async def handle(self, query: GridifyCategoryQuery) -> SearchResult[Category]:
        return await self._repository.search_gridify(
            query.filter, query.order_by, query.page, query.page_size
        )
