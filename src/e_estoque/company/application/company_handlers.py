"""Handlers CQRS de Company."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from e_estoque.company.domain.company import Company, CompanyAddress, CompanyCriteria
from e_estoque.company.domain.company import CompanyRepository
from e_estoque.shared.application.address_input import AddressInput
from e_estoque.shared.application.handlers_support import (
    ensure_found,
    ensure_valid,
    publish_events,
)
from e_estoque.shared.application.message_bus import NOTIFICATION_EXCHANGE, MessageBus
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.db import UnitOfWork

EXCHANGE = "company-service"


@dataclass(frozen=True, slots=True)
class CreateCompanyCommand:
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    company_address: AddressInput


@dataclass(frozen=True, slots=True)
class UpdateCompanyCommand:
    id: UUID
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    company_address: AddressInput


@dataclass(frozen=True, slots=True)
class DeleteCompanyCommand:
    id: UUID


@dataclass(frozen=True, slots=True)
class SearchCompanyQuery:
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
class GridifyCompanyQuery:
    filter: Optional[str] = None
    order_by: Optional[str] = None
    page: int = 1
    page_size: int = 10


class CreateCompanyHandler:
    def __init__(self, repository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: CreateCompanyCommand) -> UUID:
        company = Company.create(
            command.name, command.doc_id, command.email, command.description,
            command.phone_number, command.company_address.to_vo(CompanyAddress),
        )
        await ensure_valid(company, self._bus, "Validate Company has error", NOTIFICATION_EXCHANGE)
        await self._repository.save(company)
        await self._uow.commit()
        # Paridade: o .NET publicava os eventos de Company em `category-service`
        # (bug); aqui publica na exchange correta — MIGRATION-DIFFERENCES #1.
        await publish_events(company, self._bus, EXCHANGE)
        return company.id


class UpdateCompanyHandler:
    def __init__(self, repository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: UpdateCompanyCommand) -> UUID:
        company = await self._repository.find_by_id(command.id)
        await ensure_found(
            company, self._bus, "Update Company has error", "Find Error", NOTIFICATION_EXCHANGE
        )
        assert company is not None  # garantido por ensure_found
        company.update(
            command.name, command.doc_id, command.email, command.description,
            command.phone_number, command.company_address.to_vo(CompanyAddress),
        )
        await ensure_valid(company, self._bus, "Validate Company has error", NOTIFICATION_EXCHANGE)
        await self._repository.save(company)
        await self._uow.commit()
        await publish_events(company, self._bus, EXCHANGE)
        return company.id


class DeleteCompanyHandler:
    def __init__(self, repository, uow: UnitOfWork, bus: MessageBus) -> None:
        self._repository = repository
        self._uow = uow
        self._bus = bus

    async def handle(self, command: DeleteCompanyCommand) -> None:
        company = await self._repository.find_by_id(command.id)
        await ensure_found(
            company, self._bus, "Delete Company has error", "Delete Error", NOTIFICATION_EXCHANGE
        )
        assert company is not None  # garantido por ensure_found
        await self._repository.delete_hard(company.id)
        await self._uow.commit()


class GetByIdCompanyHandler:
    def __init__(self, repository, bus: MessageBus) -> None:
        self._repository = repository
        self._bus = bus

    async def handle(self, company_id: UUID) -> Company:
        company = await self._repository.find_by_id(company_id)
        await ensure_found(
            company, self._bus, "Not found Company", "Not found", NOTIFICATION_EXCHANGE
        )
        assert company is not None  # garantido por ensure_found
        return company


class SearchCompanyHandler:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def handle(self, query: SearchCompanyQuery) -> SearchResult[Company]:
        criteria = CompanyCriteria(
            name=query.name, doc_id=query.doc_id, email=query.email,
            description=query.description, phone_number=query.phone_number,
            id=query.id, created_at=query.created_at, updated_at=query.updated_at,
            deleted_at=query.deleted_at, order=query.order,
            page=query.page_index, size=query.page_size,
        )
        return await self._repository.search(criteria)


class GridifyCompanyHandler:
    def __init__(self, repository) -> None:
        self._repository = repository

    async def handle(self, query: GridifyCompanyQuery) -> SearchResult[Company]:
        return await self._repository.search_gridify(
            query.filter, query.order_by, query.page, query.page_size
        )
