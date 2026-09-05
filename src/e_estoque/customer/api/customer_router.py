"""Router de Customer — contrato .NET: `api/Customers` (delete soft, POST → 200)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from e_estoque.customer.application.customer_handlers import (
    CreateCustomerCommand,
    CreateCustomerHandler,
    DeleteCustomerCommand,
    DeleteCustomerHandler,
    GetByIdCustomerHandler,
    GridifyCustomerHandler,
    GridifyCustomerQuery,
    SearchCustomerHandler,
    SearchCustomerQuery,
    UpdateCustomerCommand,
    UpdateCustomerHandler,
)
from e_estoque.customer.domain.customer import CustomerRepository
from e_estoque.customer.infrastructure.customer_repository import SqlCustomerRepository
from e_estoque.shared.api.schemas import (
    BaseResult,
    BaseResultList,
    paged_search_bounds,
    paged_view,
)
from e_estoque.shared.api.security import CurrentUser, current_user, require_create
from e_estoque.shared.api.views import CustomerView
from e_estoque.shared.application.address_input import AddressInput
from e_estoque.shared.application.message_bus import MessageBus
from e_estoque.shared.infrastructure.db import UnitOfWork, open_uow

router = APIRouter(
    prefix="/api/Customers", tags=["Customers"], dependencies=[Depends(current_user)]
)


def _repository(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> CustomerRepository:
    return SqlCustomerRepository(uow.session)


def _bus(request: Request) -> MessageBus:
    bus: MessageBus = request.app.state.bus
    return bus


def _search_handler(
    repository: Annotated[CustomerRepository, Depends(_repository)],
) -> SearchCustomerHandler:
    return SearchCustomerHandler(repository)


def _gridify_handler(
    repository: Annotated[CustomerRepository, Depends(_repository)],
) -> GridifyCustomerHandler:
    return GridifyCustomerHandler(repository)


def _get_handler(
    repository: Annotated[CustomerRepository, Depends(_repository)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> GetByIdCustomerHandler:
    return GetByIdCustomerHandler(repository, bus)


def _create_handler(
    repository: Annotated[CustomerRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> CreateCustomerHandler:
    return CreateCustomerHandler(repository, uow, bus)


def _update_handler(
    repository: Annotated[CustomerRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> UpdateCustomerHandler:
    return UpdateCustomerHandler(repository, uow, bus)


def _delete_handler(
    repository: Annotated[CustomerRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> DeleteCustomerHandler:
    return DeleteCustomerHandler(repository, uow, bus)


class CustomerAddressRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    street: str
    number: str
    complement: str
    neighborhood: str
    district: str
    city: str
    country: str
    zip_code: str
    latitude: str
    longitude: str


class CreateCustomerRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    customer_address: CustomerAddressRequest


class UpdateCustomerRequest(CreateCustomerRequest):
    pass


@router.get("")
async def search(
    handler: Annotated[SearchCustomerHandler, Depends(_search_handler)],
    name: str = "",
    doc_id: Annotated[str, Query(alias="docId")] = "",
    email: str = "",
    description: str = "",
    phone_number: Annotated[str, Query(alias="phoneNumber")] = "",
    id: UUID | None = None,
    created_at: Annotated[datetime | None, Query(alias="createdAt")] = None,
    updated_at: Annotated[datetime | None, Query(alias="updatedAt")] = None,
    deleted_at: Annotated[datetime | None, Query(alias="deletedAt")] = None,
    order: str | None = None,
    page_index: Annotated[int | None, Query(alias="pageIndex", ge=1)] = None,
    page_size: Annotated[int | None, Query(alias="pageSize", ge=1)] = None,
) -> BaseResultList[CustomerView]:
    page, size = paged_search_bounds(page_index, page_size)
    result = await handler.handle(
        SearchCustomerQuery(
            name=name,
            doc_id=doc_id,
            email=email,
            description=description,
            phone_number=phone_number,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            order=order,
            page_index=page,
            page_size=size,
        )
    )
    return BaseResultList[CustomerView](
        data=[CustomerView.model_validate(c, from_attributes=True) for c in result.data],
        paged_result=paged_view(result),
    )


@router.get("/gridify")
async def search_gridify(
    handler: Annotated[GridifyCustomerHandler, Depends(_gridify_handler)],
    filter: str | None = None,  # noqa: A002 - nome do contrato Gridify
    order_by: Annotated[str | None, Query(alias="orderBy")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1)] = 10,
) -> BaseResultList[CustomerView]:
    result = await handler.handle(
        GridifyCustomerQuery(filter=filter, order_by=order_by, page=page, page_size=page_size)
    )
    return BaseResultList[CustomerView](
        data=[CustomerView.model_validate(c, from_attributes=True) for c in result.data],
        paged_result=paged_view(result),
    )


@router.get("/{customer_id}")
async def get_by_id(
    customer_id: UUID,
    handler: Annotated[GetByIdCustomerHandler, Depends(_get_handler)],
) -> BaseResult[CustomerView]:
    customer = await handler.handle(customer_id)
    return BaseResult[CustomerView](
        data=CustomerView.model_validate(customer, from_attributes=True)
    )


@router.post("")
async def create(
    payload: CreateCustomerRequest,
    create_handler: Annotated[CreateCustomerHandler, Depends(_create_handler)],
    get_handler: Annotated[GetByIdCustomerHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[CustomerView]:
    customer_id = await create_handler.handle(_to_create(payload))
    customer = await get_handler.handle(customer_id)
    return BaseResult[CustomerView](
        data=CustomerView.model_validate(customer, from_attributes=True)
    )


@router.put("/{customer_id}")
async def update(
    customer_id: UUID,
    payload: UpdateCustomerRequest,
    update_handler: Annotated[UpdateCustomerHandler, Depends(_update_handler)],
    get_handler: Annotated[GetByIdCustomerHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[CustomerView]:
    await update_handler.handle(_to_update(customer_id, payload))
    customer = await get_handler.handle(customer_id)
    return BaseResult[CustomerView](
        data=CustomerView.model_validate(customer, from_attributes=True)
    )


@router.delete("/{customer_id}")
async def delete(
    customer_id: UUID,
    handler: Annotated[DeleteCustomerHandler, Depends(_delete_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> dict[str, object]:
    await handler.handle(DeleteCustomerCommand(id=customer_id))
    return {}


def _address_of(payload: CreateCustomerRequest) -> AddressInput:
    return AddressInput(**payload.customer_address.model_dump(by_alias=False))


def _to_create(payload: CreateCustomerRequest) -> CreateCustomerCommand:
    return CreateCustomerCommand(
        name=payload.name,
        doc_id=payload.doc_id,
        email=payload.email,
        description=payload.description,
        phone_number=payload.phone_number,
        customer_address=_address_of(payload),
    )


def _to_update(customer_id: UUID, payload: UpdateCustomerRequest) -> UpdateCustomerCommand:
    return UpdateCustomerCommand(
        id=customer_id,
        name=payload.name,
        doc_id=payload.doc_id,
        email=payload.email,
        description=payload.description,
        phone_number=payload.phone_number,
        customer_address=_address_of(payload),
    )
