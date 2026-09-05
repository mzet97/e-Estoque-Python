"""Handlers CQRS de Customer (delete = soft, paridade .NET)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from e_estoque.customer.domain.customer import (
    Customer,
    CustomerAddress,
    CustomerCriteria,
    CustomerRepository,
)
from e_estoque.shared.application.address_input import AddressInput
from e_estoque.shared.application.handlers_support import (
    ensure_found,
    ensure_valid,
    publish_events,
)
from e_estoque.shared.application.message_bus import NOTIFICATION_EXCHANGE, MessageBus
from e_estoque.shared.domain.entity import utcnow
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.db import UnitOfWork

EXCHANGE = "customer-service"


@dataclass(frozen=True, slots=True)
class CreateCustomerCommand:
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    customer_address: AddressInput


@dataclass(frozen=True, slots=True)
class UpdateCustomerCommand:
    id: UUID
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    customer_address: AddressInput


@dataclass(frozen=True, slots=True)
class DeleteCustomerCommand:
    id: UUID


@dataclass(frozen=True, slots=True)
class SearchCustomerQuery:
    name: str = ""
    doc_id: str = ""
    email: str = ""
    description: str = ""
    phone_number: str = ""
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    order: Optional[str] = None
    page_index: int = 1
    page_size: int = 10


@dataclass(frozen=True, slots=True)
class GridifyCustomerQuery:
    filter: Optional[str] = None
    order_by: Optional[str] = None
    page: int = 1
    page_size: int = 10


class CreateCustomerHandler:
    def __init__(self, repository: CustomerRepository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: CreateCustomerCommand) -> UUID:
        customer = Customer.create(
            command.name, command.doc_id, command.email, command.description,
            command.phone_number, command.customer_address.to_vo(CustomerAddress),
        )
        await ensure_valid(customer, self._bus, "Validate Customer has error", NOTIFICATION_EXCHANGE)
        await self._repository.save(customer)
        await self._uow.commit()
        await publish_events(customer, self._bus, EXCHANGE)
        return customer.id


class UpdateCustomerHandler:
    def __init__(self, repository: CustomerRepository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: UpdateCustomerCommand) -> UUID:
        customer = await self._repository.find_by_id(command.id)
        await ensure_found(
            customer, self._bus, "Update Customer has error", "Find Error", NOTIFICATION_EXCHANGE
        )
        assert customer is not None  # garantido por ensure_found
        customer.update(
            command.name, command.doc_id, command.email, command.description,
            command.phone_number, command.customer_address.to_vo(CustomerAddress),
        )
        await ensure_valid(customer, self._bus, "Validate Customer has error", NOTIFICATION_EXCHANGE)
        await self._repository.save(customer)
        await self._uow.commit()
        await publish_events(customer, self._bus, EXCHANGE)
        return customer.id


class DeleteCustomerHandler:
    def __init__(self, repository: CustomerRepository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: DeleteCustomerCommand) -> None:
        customer = await self._repository.find_by_id(command.id)
        await ensure_found(
            customer, self._bus, "Delete Customer has error", "Delete Error", NOTIFICATION_EXCHANGE
        )
        assert customer is not None  # garantido por ensure_found
        # Paridade .NET: delete de Customer é soft (DisableAsync).
        await self._repository.disable(customer.id, utcnow())
        await self._uow.commit()


class GetByIdCustomerHandler:
    def __init__(self, repository: CustomerRepository, bus: MessageBus) -> None:
        self._repository = repository
        self._bus = bus

    async def handle(self, customer_id: UUID) -> Customer:
        customer = await self._repository.find_by_id(customer_id)
        await ensure_found(
            customer, self._bus, "Not found Customer", "Not found", NOTIFICATION_EXCHANGE
        )
        assert customer is not None  # garantido por ensure_found
        return customer


class SearchCustomerHandler:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    async def handle(self, query: SearchCustomerQuery) -> SearchResult[Customer]:
        criteria = CustomerCriteria(
            name=query.name, doc_id=query.doc_id, email=query.email,
            description=query.description, phone_number=query.phone_number,
            id=query.id, created_at=query.created_at, updated_at=query.updated_at,
            deleted_at=query.deleted_at,
            order=query.order, page=query.page_index, size=query.page_size,
        )
        return await self._repository.search(criteria)


class GridifyCustomerHandler:
    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    async def handle(self, query: GridifyCustomerQuery) -> SearchResult[Customer]:
        return await self._repository.search_gridify(
            query.filter, query.order_by, query.page, query.page_size
        )
