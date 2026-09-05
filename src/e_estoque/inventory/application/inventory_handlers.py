"""Handlers CQRS de Inventory.

Paridades .NET: validação de domínio ANTES da checagem de produto; produto
inexistente → NotFoundError("Product not found").
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from e_estoque.inventory.domain.inventory import (
    Inventory,
    InventoryCriteria,
    InventoryRepository,
    ProductReader,
)
from e_estoque.shared.application.handlers_support import (
    ensure_found,
    ensure_valid,
    publish_events,
)
from e_estoque.shared.application.message_bus import NOTIFICATION_EXCHANGE, MessageBus
from e_estoque.shared.application.read_models import Detailed
from e_estoque.shared.application.unit_of_work import UnitOfWork
from e_estoque.shared.domain.errors import NotFoundError
from e_estoque.shared.domain.search import SearchResult

EXCHANGE = "inventory-service"


@dataclass(frozen=True, slots=True)
class CreateInventoryCommand:
    quantity: int
    date_order: datetime
    id_product: UUID


@dataclass(frozen=True, slots=True)
class UpdateInventoryCommand:
    id: UUID
    quantity: int
    date_order: datetime
    id_product: UUID


@dataclass(frozen=True, slots=True)
class DeleteInventoryCommand:
    id: UUID


@dataclass(frozen=True, slots=True)
class SearchInventoryQuery:
    quantity: int | None = None
    date_order: datetime | None = None
    id_product: UUID | None = None
    id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    order: str | None = None
    page_index: int = 1
    page_size: int = 10


@dataclass(frozen=True, slots=True)
class GridifyInventoryQuery:
    filter: str | None = None
    order_by: str | None = None
    page: int = 1
    page_size: int = 10


class CreateInventoryHandler:
    def __init__(
        self,
        repository: InventoryRepository,
        uow: UnitOfWork,
        bus: MessageBus,
        product_reader: ProductReader,
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus
        self._product_reader = product_reader

    async def handle(self, command: CreateInventoryCommand) -> UUID:
        inventory = Inventory.create(command.quantity, command.date_order, command.id_product)
        await ensure_valid(
            inventory, self._bus, "Validate Inventory has error", NOTIFICATION_EXCHANGE
        )
        if not await self._product_reader.exists(command.id_product):
            await self._bus.publish_notification_error(
                "Product not found", "Product not found", NOTIFICATION_EXCHANGE
            )
            raise NotFoundError("Product not found")
        await self._repository.save(inventory)
        await self._uow.commit()
        await publish_events(inventory, self._bus, EXCHANGE)
        return inventory.id


class UpdateInventoryHandler:
    def __init__(
        self,
        repository: InventoryRepository,
        uow: UnitOfWork,
        bus: MessageBus,
        product_reader: ProductReader,
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus
        self._product_reader = product_reader

    async def handle(self, command: UpdateInventoryCommand) -> UUID:
        inventory = await self._repository.find_by_id(command.id)
        await ensure_found(
            inventory,
            self._bus,
            "Update Inventory has error",
            "Find Error",
            NOTIFICATION_EXCHANGE,
        )
        assert inventory is not None  # garantido por ensure_found
        if not await self._product_reader.exists(command.id_product):
            await self._bus.publish_notification_error(
                "Product not found", "Product not found", NOTIFICATION_EXCHANGE
            )
            raise NotFoundError("Product not found")
        inventory.update(command.quantity, command.date_order, command.id_product)
        await ensure_valid(
            inventory, self._bus, "Validate Inventory has error", NOTIFICATION_EXCHANGE
        )
        await self._repository.save(inventory)
        await self._uow.commit()
        await publish_events(inventory, self._bus, EXCHANGE)
        return inventory.id


class DeleteInventoryHandler:
    def __init__(self, repository: InventoryRepository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: DeleteInventoryCommand) -> None:
        inventory = await self._repository.find_by_id(command.id)
        await ensure_found(
            inventory,
            self._bus,
            "Delete Inventory has error",
            "Delete Error",
            NOTIFICATION_EXCHANGE,
        )
        assert inventory is not None  # garantido por ensure_found
        await self._repository.delete_hard(inventory.id)
        await self._uow.commit()


class GetByIdInventoryHandler:
    def __init__(self, repository: InventoryRepository, bus: MessageBus) -> None:
        self._repository = repository
        self._bus = bus

    async def handle(self, inventory_id: UUID) -> Detailed[Inventory]:
        detailed = await self._repository.find_detailed_by_id(inventory_id)
        await ensure_found(
            detailed, self._bus, "Not found Inventory", "Not found", NOTIFICATION_EXCHANGE
        )
        assert detailed is not None  # garantido por ensure_found
        return detailed


class SearchInventoryHandler:
    def __init__(self, repository: InventoryRepository) -> None:
        self._repository = repository

    async def handle(self, query: SearchInventoryQuery) -> SearchResult[Detailed[Inventory]]:
        criteria = InventoryCriteria(
            quantity=query.quantity,
            date_order=query.date_order,
            id_product=query.id_product,
            id=query.id,
            created_at=query.created_at,
            updated_at=query.updated_at,
            deleted_at=query.deleted_at,
            order=query.order,
            page=query.page_index,
            size=query.page_size,
        )
        return await self._repository.search(criteria)


class GridifyInventoryHandler:
    def __init__(self, repository: InventoryRepository) -> None:
        self._repository = repository

    async def handle(self, query: GridifyInventoryQuery) -> SearchResult[Detailed[Inventory]]:
        return await self._repository.search_gridify(
            query.filter, query.order_by, query.page, query.page_size
        )
