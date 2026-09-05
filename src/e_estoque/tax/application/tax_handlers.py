"""Handlers CQRS de Tax.

Paridades .NET: categoria inexistente → ValidationException (400, não 404);
update not-found → "Tax not found".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from e_estoque.shared.application.handlers_support import (
    ensure_found,
    ensure_valid,
    publish_events,
)
from e_estoque.shared.application.message_bus import NOTIFICATION_EXCHANGE, MessageBus
from e_estoque.shared.application.read_models import Detailed
from e_estoque.shared.application.unit_of_work import UnitOfWork
from e_estoque.shared.domain.errors import ValidationError
from e_estoque.shared.domain.search import SearchResult
from e_estoque.tax.domain.tax import CategoryReader, Tax, TaxCriteria, TaxRepository

EXCHANGE = "tax-service"


@dataclass(frozen=True, slots=True)
class CreateTaxCommand:
    name: str
    description: str
    percentage: Decimal
    id_category: UUID


@dataclass(frozen=True, slots=True)
class UpdateTaxCommand:
    id: UUID
    name: str
    description: str
    percentage: Decimal
    id_category: UUID


@dataclass(frozen=True, slots=True)
class DeleteTaxCommand:
    id: UUID


@dataclass(frozen=True, slots=True)
class SearchTaxQuery:
    name: str = ""
    description: str = ""
    percentage: Decimal | None = None
    id_category: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    order: str | None = None
    page_index: int = 1
    page_size: int = 10


@dataclass(frozen=True, slots=True)
class GridifyTaxQuery:
    filter: str | None = None
    order_by: str | None = None
    page: int = 1
    page_size: int = 10


class CreateTaxHandler:
    def __init__(
        self,
        repository: TaxRepository,
        uow: UnitOfWork,
        bus: MessageBus,
        category_reader: CategoryReader,
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus
        self._category_reader = category_reader

    async def handle(self, command: CreateTaxCommand) -> UUID:
        tax = Tax.create(command.name, command.description, command.percentage, command.id_category)
        await ensure_valid(tax, self._bus, "Validate Tax has error", NOTIFICATION_EXCHANGE)
        # Paridade .NET: categoria inexistente em Tax lança ValidationException (400).
        if not await self._category_reader.exists(command.id_category):
            await self._bus.publish_notification_error(
                "Category not found", "Category not found", NOTIFICATION_EXCHANGE
            )
            raise ValidationError("Category not found")
        await self._repository.save(tax)
        await self._uow.commit()
        await publish_events(tax, self._bus, EXCHANGE)
        return tax.id


class UpdateTaxHandler:
    def __init__(
        self,
        repository: TaxRepository,
        uow: UnitOfWork,
        bus: MessageBus,
        category_reader: CategoryReader,
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus
        self._category_reader = category_reader

    async def handle(self, command: UpdateTaxCommand) -> UUID:
        tax = await self._repository.find_by_id(command.id)
        await ensure_found(
            tax, self._bus, "Update Tax has error", "Tax not found", NOTIFICATION_EXCHANGE
        )
        assert tax is not None  # garantido por ensure_found
        if not await self._category_reader.exists(command.id_category):
            await self._bus.publish_notification_error(
                "Category not found", "Category not found", NOTIFICATION_EXCHANGE
            )
            raise ValidationError("Category not found")
        tax.update(command.name, command.description, command.percentage, command.id_category)
        await ensure_valid(tax, self._bus, "Validate Tax has error", NOTIFICATION_EXCHANGE)
        await self._repository.save(tax)
        await self._uow.commit()
        await publish_events(tax, self._bus, EXCHANGE)
        return tax.id


class DeleteTaxHandler:
    def __init__(self, repository: TaxRepository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: DeleteTaxCommand) -> None:
        tax = await self._repository.find_by_id(command.id)
        await ensure_found(
            tax, self._bus, "Delete Tax has error", "Delete Error", NOTIFICATION_EXCHANGE
        )
        assert tax is not None  # garantido por ensure_found
        await self._repository.delete_hard(tax.id)
        await self._uow.commit()


class GetByIdTaxHandler:
    def __init__(self, repository: TaxRepository, bus: MessageBus) -> None:
        self._repository = repository
        self._bus = bus

    async def handle(self, tax_id: UUID) -> Detailed[Tax]:
        detailed = await self._repository.find_detailed_by_id(tax_id)
        await ensure_found(detailed, self._bus, "Not found Tax", "Not found", NOTIFICATION_EXCHANGE)
        assert detailed is not None  # garantido por ensure_found
        return detailed


class SearchTaxHandler:
    def __init__(self, repository: TaxRepository) -> None:
        self._repository = repository

    async def handle(self, query: SearchTaxQuery) -> SearchResult[Detailed[Tax]]:
        criteria = TaxCriteria(
            name=query.name,
            description=query.description,
            percentage=query.percentage,
            id_category=query.id_category,
            created_at=query.created_at,
            updated_at=query.updated_at,
            deleted_at=query.deleted_at,
            order=query.order,
            page=query.page_index,
            size=query.page_size,
        )
        return await self._repository.search(criteria)


class GridifyTaxHandler:
    def __init__(self, repository: TaxRepository) -> None:
        self._repository = repository

    async def handle(self, query: GridifyTaxQuery) -> SearchResult[Detailed[Tax]]:
        return await self._repository.search_gridify(
            query.filter, query.order_by, query.page, query.page_size
        )
