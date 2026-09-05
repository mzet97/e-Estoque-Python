"""Inventory: entidade, eventos, critérios e porta de repositório."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from e_estoque.shared.application.read_models import Detailed
from e_estoque.shared.domain.checks import audit, positive, provided, provided_number
from e_estoque.shared.domain.entity import DomainEvent, Entity, utcnow
from e_estoque.shared.domain.search import SearchResult

EXCHANGE = "inventory-service"


# ---- Domain Events ----
@dataclass(frozen=True, slots=True)
class InventoryCreated(DomainEvent):
    id: UUID
    quantity: int
    date_order: datetime
    id_product: UUID
    occurred_on: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class InventoryUpdated(DomainEvent):
    id: UUID
    quantity: int
    date_order: datetime
    id_product: UUID
    occurred_on: datetime = field(default_factory=utcnow)


# ---- Entity ----
class Inventory(Entity):
    __slots__ = ("quantity", "date_order", "id_product")

    def __init__(
        self,
        id: UUID,  # noqa: A002
        quantity: int,
        date_order: datetime,
        id_product: UUID,
        created_at: datetime,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
        is_deleted: bool = False,
    ) -> None:
        super().__init__(id, created_at, updated_at, deleted_at, is_deleted)
        self.quantity = quantity
        self.date_order = date_order
        self.id_product = id_product

    @classmethod
    def create(cls, quantity: int, date_order: datetime, id_product: UUID) -> Inventory:
        inventory = cls(uuid4(), quantity, date_order, id_product, utcnow())
        inventory.register_event(InventoryCreated(inventory.id, quantity, date_order, id_product))
        inventory.validate()
        return inventory

    @classmethod
    def rehydrate(
        cls,
        id: UUID,  # noqa: A002
        quantity: int,
        date_order: datetime,
        id_product: UUID,
        created_at: datetime,
        updated_at: datetime | None,
        deleted_at: datetime | None,
        is_deleted: bool,
    ) -> Inventory:
        inventory = cls(
            id, quantity, date_order, id_product, created_at, updated_at, deleted_at, is_deleted
        )
        inventory.validate()
        return inventory

    def update(self, quantity: int, date_order: datetime, id_product: UUID) -> None:
        self.quantity = quantity
        self.date_order = date_order
        self.id_product = id_product
        self.touch(utcnow())
        self.register_event(InventoryUpdated(self.id, quantity, date_order, id_product))
        self.validate()

    def validate(self) -> None:
        errors: list[str] = []
        audit(self.id, self.created_at, self.updated_at, self.deleted_at, errors)
        provided_number(errors, self.quantity, "Quantity")
        positive(errors, self.quantity, "Quantity")
        provided(errors, self.date_order, "DateOrder")
        provided(errors, self.id_product, "IdProduct")
        if errors:
            self.mark_invalid(errors)
        else:
            self.mark_valid()


# ---- Criteria / Port ----
@dataclass(frozen=True, slots=True)
class InventoryCriteria:
    id: UUID | None = None
    quantity: int | None = None
    date_order: datetime | None = None
    id_product: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    order: str | None = None
    page: int = 1
    size: int = 10


class ProductReader(Protocol):
    """Verificação de existência de Product (referencial do Inventory)."""

    async def exists(self, product_id: UUID) -> bool: ...


class InventoryRepository(Protocol):
    async def save(self, inventory: Inventory) -> None: ...

    async def find_by_id(self, inventory_id: UUID) -> Inventory | None: ...

    async def find_detailed_by_id(self, inventory_id: UUID) -> Detailed[Inventory] | None: ...

    async def search(self, criteria: InventoryCriteria) -> SearchResult[Detailed[Inventory]]: ...

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Detailed[Inventory]]: ...

    async def delete_hard(self, inventory_id: UUID) -> None: ...
