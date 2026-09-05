"""Handlers CQRS de Product.

Paridades .NET: categoria/empresa inexistentes → NotFoundError (404).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from e_estoque.product.domain.product import (
    CategoryReader,
    CompanyReader,
    Product,
    ProductCriteria,
    ProductRepository,
)
from e_estoque.shared.application.handlers_support import (
    ensure_found,
    ensure_valid,
    publish_events,
)
from e_estoque.shared.application.message_bus import NOTIFICATION_EXCHANGE, MessageBus
from e_estoque.shared.application.read_models import Detailed
from e_estoque.shared.domain.errors import NotFoundError
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.db import UnitOfWork

EXCHANGE = "product-service"


@dataclass(frozen=True, slots=True)
class CreateProductCommand:
    name: str
    description: str
    short_description: str
    price: Decimal
    weight: Decimal
    height: Decimal
    length: Decimal
    image: str
    id_category: UUID
    id_company: UUID


@dataclass(frozen=True, slots=True)
class UpdateProductCommand:
    id: UUID
    name: str
    description: str
    short_description: str
    price: Decimal
    weight: Decimal
    height: Decimal
    length: Decimal
    image: str
    id_category: UUID
    id_company: UUID


@dataclass(frozen=True, slots=True)
class DeleteProductCommand:
    id: UUID


@dataclass(frozen=True, slots=True)
class SearchProductQuery:
    name: str = ""
    description: str = ""
    short_description: str = ""
    price: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    height: Optional[Decimal] = None
    length: Optional[Decimal] = None
    id_category: Optional[UUID] = None
    id_company: Optional[UUID] = None
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    order: Optional[str] = None
    page_index: int = 1
    page_size: int = 10


@dataclass(frozen=True, slots=True)
class GridifyProductQuery:
    filter: Optional[str] = None
    order_by: Optional[str] = None
    page: int = 1
    page_size: int = 10


class CreateProductHandler:
    def __init__(
        self,
        repository: ProductRepository,
        uow: UnitOfWork,
        bus: MessageBus,
        category_reader: CategoryReader,
        company_reader: CompanyReader,
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus
        self._category_reader = category_reader
        self._company_reader = company_reader

    async def handle(self, command: CreateProductCommand) -> UUID:
        product = Product.create(
            command.name, command.description, command.short_description,
            command.price, command.weight, command.height, command.length,
            command.image, command.id_category, command.id_company,
        )
        await ensure_valid(product, self._bus, "Validate Product has error", NOTIFICATION_EXCHANGE)
        if not await self._category_reader.exists(command.id_category):
            await self._bus.publish_notification_error(
                "Category not found", "Category not found", NOTIFICATION_EXCHANGE
            )
            raise NotFoundError("Category not found")
        if not await self._company_reader.exists(command.id_company):
            await self._bus.publish_notification_error(
                "Company not found", "Company not found", NOTIFICATION_EXCHANGE
            )
            raise NotFoundError("Company not found")
        await self._repository.save(product)
        await self._uow.commit()
        await publish_events(product, self._bus, EXCHANGE)
        return product.id


class UpdateProductHandler:
    def __init__(
        self,
        repository: ProductRepository,
        uow: UnitOfWork,
        bus: MessageBus,
        category_reader: CategoryReader,
        company_reader: CompanyReader,
    ) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus
        self._category_reader = category_reader
        self._company_reader = company_reader

    async def handle(self, command: UpdateProductCommand) -> UUID:
        product = await self._repository.find_by_id(command.id)
        await ensure_found(
            product, self._bus, "Update Product has error", "Find Error", NOTIFICATION_EXCHANGE
        )
        assert product is not None  # garantido por ensure_found
        if not await self._category_reader.exists(command.id_category):
            await self._bus.publish_notification_error(
                "Category not found", "Category not found", NOTIFICATION_EXCHANGE
            )
            raise NotFoundError("Category not found")
        if not await self._company_reader.exists(command.id_company):
            await self._bus.publish_notification_error(
                "Company not found", "Company not found", NOTIFICATION_EXCHANGE
            )
            raise NotFoundError("Company not found")
        product.update(
            command.name, command.description, command.short_description,
            command.price, command.weight, command.height, command.length,
            command.image, command.id_category, command.id_company,
        )
        await ensure_valid(product, self._bus, "Validate Product has error", NOTIFICATION_EXCHANGE)
        await self._repository.save(product)
        await self._uow.commit()
        await publish_events(product, self._bus, EXCHANGE)
        return product.id


class DeleteProductHandler:
    def __init__(self, repository: ProductRepository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: DeleteProductCommand) -> None:
        product = await self._repository.find_by_id(command.id)
        await ensure_found(
            product, self._bus, "Delete Product has error", "Delete Error", NOTIFICATION_EXCHANGE
        )
        assert product is not None  # garantido por ensure_found
        await self._repository.delete_hard(product.id)
        await self._uow.commit()


class GetByIdProductHandler:
    def __init__(self, repository: ProductRepository, bus: MessageBus) -> None:
        self._repository = repository
        self._bus = bus

    async def handle(self, product_id: UUID) -> Detailed[Product]:
        detailed = await self._repository.find_detailed_by_id(product_id)
        await ensure_found(
            detailed, self._bus, "Not found Product", "Not found", NOTIFICATION_EXCHANGE
        )
        assert detailed is not None  # garantido por ensure_found
        return detailed


class SearchProductHandler:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def handle(self, query: SearchProductQuery) -> SearchResult[Detailed[Product]]:
        criteria = ProductCriteria(
            name=query.name, description=query.description,
            short_description=query.short_description,
            price=query.price, weight=query.weight, height=query.height,
            length=query.length, id_category=query.id_category,
            id_company=query.id_company, id=query.id,
            created_at=query.created_at, updated_at=query.updated_at,
            deleted_at=query.deleted_at,
            order=query.order, page=query.page_index, size=query.page_size,
        )
        return await self._repository.search(criteria)


class GridifyProductHandler:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def handle(self, query: GridifyProductQuery) -> SearchResult[Detailed[Product]]:
        return await self._repository.search_gridify(
            query.filter, query.order_by, query.page, query.page_size
        )
