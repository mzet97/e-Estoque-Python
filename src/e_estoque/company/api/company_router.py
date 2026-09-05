"""Router de Company — contrato .NET: `api/Companies` (POST → 200)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from e_estoque.company.application.company_handlers import (
    CreateCompanyCommand,
    CreateCompanyHandler,
    DeleteCompanyCommand,
    DeleteCompanyHandler,
    GetByIdCompanyHandler,
    GridifyCompanyHandler,
    GridifyCompanyQuery,
    SearchCompanyHandler,
    SearchCompanyQuery,
    UpdateCompanyCommand,
    UpdateCompanyHandler,
)
from e_estoque.company.domain.company import CompanyRepository
from e_estoque.company.infrastructure.company_repository import SqlCompanyRepository
from e_estoque.shared.api.schemas import (
    BaseResult,
    BaseResultList,
    paged_search_bounds,
    paged_view,
)
from e_estoque.shared.api.security import CurrentUser, current_user, require_create
from e_estoque.shared.api.views import CompanyView
from e_estoque.shared.application.address_input import AddressInput
from e_estoque.shared.application.message_bus import MessageBus
from e_estoque.shared.infrastructure.db import UnitOfWork, open_uow

router = APIRouter(
    prefix="/api/Companies", tags=["Companies"], dependencies=[Depends(current_user)]
)


# ---- dependências ----
def _repository(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> CompanyRepository:
    return SqlCompanyRepository(uow.session)


def _bus(request: Request) -> MessageBus:
    bus: MessageBus = request.app.state.bus
    return bus


def _search_handler(
    repository: Annotated[CompanyRepository, Depends(_repository)],
) -> SearchCompanyHandler:
    return SearchCompanyHandler(repository)


def _gridify_handler(
    repository: Annotated[CompanyRepository, Depends(_repository)],
) -> GridifyCompanyHandler:
    return GridifyCompanyHandler(repository)


def _get_handler(
    repository: Annotated[CompanyRepository, Depends(_repository)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> GetByIdCompanyHandler:
    return GetByIdCompanyHandler(repository, bus)


def _create_handler(
    repository: Annotated[CompanyRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> CreateCompanyHandler:
    return CreateCompanyHandler(repository, uow, bus)


def _update_handler(
    repository: Annotated[CompanyRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> UpdateCompanyHandler:
    return UpdateCompanyHandler(repository, uow, bus)


def _delete_handler(
    repository: Annotated[CompanyRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> DeleteCompanyHandler:
    return DeleteCompanyHandler(repository, uow, bus)


# ---- request bodies ----
class CompanyAddressRequest(BaseModel):
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


class CreateCompanyRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    company_address: CompanyAddressRequest


class UpdateCompanyRequest(CreateCompanyRequest):
    pass


# ---- endpoints ----
@router.get("")
async def search(
    handler: Annotated[SearchCompanyHandler, Depends(_search_handler)],
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
) -> BaseResultList[CompanyView]:
    page, size = paged_search_bounds(page_index, page_size)
    result = await handler.handle(
        SearchCompanyQuery(
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
    return BaseResultList[CompanyView](
        data=[CompanyView.model_validate(c, from_attributes=True) for c in result.data],
        paged_result=paged_view(result),
    )


@router.get("/gridify")
async def search_gridify(
    handler: Annotated[GridifyCompanyHandler, Depends(_gridify_handler)],
    filter: str | None = None,  # noqa: A002 - nome do contrato Gridify
    order_by: Annotated[str | None, Query(alias="orderBy")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1)] = 10,
) -> BaseResultList[CompanyView]:
    result = await handler.handle(
        GridifyCompanyQuery(filter=filter, order_by=order_by, page=page, page_size=page_size)
    )
    return BaseResultList[CompanyView](
        data=[CompanyView.model_validate(c, from_attributes=True) for c in result.data],
        paged_result=paged_view(result),
    )


@router.get("/{company_id}")
async def get_by_id(
    company_id: UUID,
    handler: Annotated[GetByIdCompanyHandler, Depends(_get_handler)],
) -> BaseResult[CompanyView]:
    company = await handler.handle(company_id)
    return BaseResult[CompanyView](data=CompanyView.model_validate(company, from_attributes=True))


@router.post("")
async def create(
    payload: CreateCompanyRequest,
    create_handler: Annotated[CreateCompanyHandler, Depends(_create_handler)],
    get_handler: Annotated[GetByIdCompanyHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[CompanyView]:
    company_id = await create_handler.handle(_to_create(payload))
    company = await get_handler.handle(company_id)
    return BaseResult[CompanyView](data=CompanyView.model_validate(company, from_attributes=True))


@router.put("/{company_id}")
async def update(
    company_id: UUID,
    payload: UpdateCompanyRequest,
    update_handler: Annotated[UpdateCompanyHandler, Depends(_update_handler)],
    get_handler: Annotated[GetByIdCompanyHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[CompanyView]:
    await update_handler.handle(_to_update(company_id, payload))
    company = await get_handler.handle(company_id)
    return BaseResult[CompanyView](data=CompanyView.model_validate(company, from_attributes=True))


@router.delete("/{company_id}")
async def delete(
    company_id: UUID,
    handler: Annotated[DeleteCompanyHandler, Depends(_delete_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> dict[str, object]:
    await handler.handle(DeleteCompanyCommand(id=company_id))
    return {}


def _address_of(payload: CreateCompanyRequest) -> AddressInput:
    return AddressInput(**payload.company_address.model_dump(by_alias=False))


def _to_create(payload: CreateCompanyRequest) -> CreateCompanyCommand:
    return CreateCompanyCommand(
        name=payload.name,
        doc_id=payload.doc_id,
        email=payload.email,
        description=payload.description,
        phone_number=payload.phone_number,
        company_address=_address_of(payload),
    )


def _to_update(company_id: UUID, payload: UpdateCompanyRequest) -> UpdateCompanyCommand:
    return UpdateCompanyCommand(
        id=company_id,
        name=payload.name,
        doc_id=payload.doc_id,
        email=payload.email,
        description=payload.description,
        phone_number=payload.phone_number,
        company_address=_address_of(payload),
    )
