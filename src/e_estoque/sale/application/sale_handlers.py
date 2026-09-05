"""Handlers CQRS de Sale.

Paridades .NET: cliente/produto inexistentes → NotFoundError; delete soft com
mensagem "Sale not found"; SaleType/PaymentType com fallback no parse (search).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from e_estoque.sale.domain.sale import (
    CustomerReader,
    PaymentType,
    ProductReader,
    Sale,
    SaleCriteria,
    SaleRepository,
    SaleType,
)
from e_estoque.shared.application.handlers_support import (
    ensure_found,
    ensure_valid,
    publish_events,
)
from e_estoque.shared.application.message_bus import (
    NOTIFICATION_EXCHANGE,
    NOTIFICATION_EXCHANGE_SALES,
    MessageBus,
)
from e_estoque.shared.application.read_models import Detailed
from e_estoque.shared.domain.errors import NotFoundError
from e_estoque.shared.domain.entity import utcnow
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.db import UnitOfWork

EXCHANGE = "sale-service"


@dataclass(frozen=True, slots=True)
class CreateSaleCommand:
    quantity: int
    total_price: Decimal
    total_tax: Decimal
    sale_type: int
    payment_type: int
    delivery_date: datetime
    sale_date: datetime
    payment_date: datetime
    id_customer: UUID
    ids_products: list[UUID]


@dataclass(frozen=True, slots=True)
class UpdateSaleCommand:
    id: UUID
    quantity: int
    total_price: Decimal
    total_tax: Decimal
    sale_type: int
    payment_type: int
    delivery_date: datetime
    sale_date: datetime
    payment_date: datetime
    id_customer: UUID
    ids_products: list[UUID]


@dataclass(frozen=True, slots=True)
class DeleteSaleCommand:
    id: UUID


@dataclass(frozen=True, slots=True)
class SearchSaleQuery:
    quantity: Optional[int] = None
    total_price: Optional[Decimal] = None
    total_tax: Optional[Decimal] = None
    sale_type: str = ""
    payment_type: str = ""
    delivery_date: Optional[datetime] = None
    sale_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    id_product: Optional[UUID] = None
    id_customer: Optional[UUID] = None
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    order: Optional[str] = None
    page_index: int = 1
    page_size: int = 10


@dataclass(frozen=True, slots=True)
class GridifySaleQuery:
    filter: Optional[str] = None
    order_by: Optional[str] = None
    page: int = 1
    page_size: int = 10


class CreateSaleHandler:
    def __init__(
        self,
        repository: SaleRepository,
        uow: UnitOfWork,
        bus: MessageBus,
        customer_reader: CustomerReader,
        product_reader: ProductReader,
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus
        self._customer_reader = customer_reader
        self._product_reader = product_reader

    async def handle(self, command: CreateSaleCommand) -> UUID:
        # Paridade .NET: parâmetros de enum chegam como int (1..4).
        sale = Sale.create(
            command.quantity, command.total_price, command.total_tax,
            _sale_type(command.sale_type), _payment_type(command.payment_type),
            command.delivery_date, command.sale_date, command.payment_date,
            command.id_customer, command.ids_products,
        )
        await ensure_valid(
            sale, self._bus, "Validate Sales has error", NOTIFICATION_EXCHANGE_SALES
        )
        if not await self._customer_reader.exists(command.id_customer):
            await self._bus.publish_notification_error(
                "Customer not found", "Customer not found", NOTIFICATION_EXCHANGE_SALES
            )
            raise NotFoundError("Customer not found")
        for product_id in command.ids_products:
            if not await self._product_reader.exists(product_id):
                await self._bus.publish_notification_error(
                    "Product not found", "Product not found", NOTIFICATION_EXCHANGE_SALES
                )
                raise NotFoundError("Product not found")
        await self._repository.save(sale)
        await self._uow.commit()
        await publish_events(sale, self._bus, EXCHANGE)
        return sale.id


class UpdateSaleHandler:
    def __init__(
        self,
        repository: SaleRepository,
        uow: UnitOfWork,
        bus: MessageBus,
        customer_reader: CustomerReader,
        product_reader: ProductReader,
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus
        self._customer_reader = customer_reader
        self._product_reader = product_reader

    async def handle(self, command: UpdateSaleCommand) -> UUID:
        sale = await self._repository.find_by_id(command.id)
        # Paridade .NET: update de venda inexistente notifica/lança "Sale not found".
        if sale is None:
            await self._bus.publish_notification_error(
                "Sale not found", "Sale not found", NOTIFICATION_EXCHANGE_SALES
            )
            raise NotFoundError("Sale not found")
        if not await self._customer_reader.exists(command.id_customer):
            await self._bus.publish_notification_error(
                "Customer not found", "Customer not found", NOTIFICATION_EXCHANGE_SALES
            )
            raise NotFoundError("Customer not found")
        for product_id in command.ids_products:
            if not await self._product_reader.exists(product_id):
                await self._bus.publish_notification_error(
                    "Product not found", "Product not found", NOTIFICATION_EXCHANGE_SALES
                )
                raise NotFoundError("Product not found")
        sale.update(
            command.quantity, command.total_price, command.total_tax,
            _sale_type(command.sale_type), _payment_type(command.payment_type),
            command.delivery_date, command.sale_date, command.payment_date,
            command.id_customer, command.ids_products,
        )
        await ensure_valid(
            sale, self._bus, "Validate Sales has error", NOTIFICATION_EXCHANGE_SALES
        )
        await self._repository.save(sale)
        await self._uow.commit()
        await publish_events(sale, self._bus, EXCHANGE)
        return sale.id


class DeleteSaleHandler:
    def __init__(self, repository: SaleRepository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: DeleteSaleCommand) -> None:
        deleted = await self._repository.disable(command.id, utcnow())
        if not deleted:
            await self._bus.publish_notification_error(
                "Delete Sale has error", "Delete Sale has error", NOTIFICATION_EXCHANGE_SALES
            )
            raise NotFoundError("Sale not found")
        await self._uow.commit()


class GetByIdSaleHandler:
    def __init__(self, repository: SaleRepository, bus: MessageBus) -> None:
        self._repository = repository
        self._bus = bus

    async def handle(self, sale_id: UUID) -> Detailed[Sale]:
        detailed = await self._repository.find_detailed_by_id(sale_id)
        await ensure_found(
            detailed, self._bus, "Sale not found", "Not found", NOTIFICATION_EXCHANGE_SALES
        )
        assert detailed is not None  # garantido por ensure_found
        return detailed


class SearchSaleHandler:
    def __init__(self, repository: SaleRepository) -> None:
        self._repository = repository

    async def handle(self, query: SearchSaleQuery) -> SearchResult[Detailed[Sale]]:
        criteria = SaleCriteria(
            quantity=query.quantity, total_price=query.total_price,
            total_tax=query.total_tax, sale_type=query.sale_type,
            payment_type=query.payment_type, delivery_date=query.delivery_date,
            sale_date=query.sale_date, payment_date=query.payment_date,
            id_product=query.id_product, id_customer=query.id_customer,
            id=query.id,
            created_at=query.created_at, updated_at=query.updated_at,
            deleted_at=query.deleted_at,
            order=query.order, page=query.page_index, size=query.page_size,
        )
        return await self._repository.search(criteria)


class GridifySaleHandler:
    def __init__(self, repository: SaleRepository) -> None:
        self._repository = repository

    async def handle(self, query: GridifySaleQuery) -> SearchResult[Detailed[Sale]]:
        return await self._repository.search_gridify(
            query.filter, query.order_by, query.page, query.page_size
        )


def _sale_type(value: int) -> "SaleType":
    try:
        return SaleType(value)
    except ValueError as exc:
        raise NotFoundError(f"Invalid saleType: {value}") from exc


def _payment_type(value: int) -> "PaymentType":
    try:
        return PaymentType(value)
    except ValueError as exc:
        raise NotFoundError(f"Invalid paymentType: {value}") from exc
