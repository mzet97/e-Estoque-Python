"""Router de Tax — contrato .NET: `api/Taxs` (POST → 200; categoria inexistente → 400)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from e_estoque.product.infrastructure.category_repository import SqlCategoryRepository
from e_estoque.shared.api.schemas import (
    BaseResult,
    BaseResultList,
    paged_search_bounds,
    paged_view,
)
from e_estoque.shared.api.security import CurrentUser, current_user, require_create
from e_estoque.shared.api.views import tax_view
from e_estoque.shared.application.message_bus import MessageBus
from e_estoque.shared.infrastructure.db import UnitOfWork, open_uow
from e_estoque.tax.application.tax_handlers import (
    CreateTaxCommand,
    CreateTaxHandler,
    DeleteTaxCommand,
    DeleteTaxHandler,
    GetByIdTaxHandler,
    GridifyTaxHandler,
    GridifyTaxQuery,
    SearchTaxHandler,
    SearchTaxQuery,
    UpdateTaxCommand,
    UpdateTaxHandler,
)
from e_estoque.tax.domain.tax import CategoryReader, TaxRepository
from e_estoque.tax.infrastructure.tax_repository import SqlTaxRepository

router = APIRouter(prefix="/api/Taxs", tags=["Taxs"], dependencies=[Depends(current_user)])


def _repository(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> TaxRepository:
    return SqlTaxRepository(uow.session)


def _bus(request: Request) -> MessageBus:
    bus: MessageBus = request.app.state.bus
    return bus


def _category_reader(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> CategoryReader:
    return SqlCategoryRepository(uow.session)


def _search_handler(
    repository: Annotated[TaxRepository, Depends(_repository)],
) -> SearchTaxHandler:
    return SearchTaxHandler(repository)


def _gridify_handler(
    repository: Annotated[TaxRepository, Depends(_repository)],
) -> GridifyTaxHandler:
    return GridifyTaxHandler(repository)


def _get_handler(
    repository: Annotated[TaxRepository, Depends(_repository)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> GetByIdTaxHandler:
    return GetByIdTaxHandler(repository, bus)


def _create_handler(
    repository: Annotated[TaxRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
    category_reader: Annotated[CategoryReader, Depends(_category_reader)],
) -> CreateTaxHandler:
    return CreateTaxHandler(repository, uow, bus, category_reader)


def _update_handler(
    repository: Annotated[TaxRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
    category_reader: Annotated[CategoryReader, Depends(_category_reader)],
) -> UpdateTaxHandler:
    return UpdateTaxHandler(repository, uow, bus, category_reader)


def _delete_handler(
    repository: Annotated[TaxRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> DeleteTaxHandler:
    return DeleteTaxHandler(repository, uow, bus)


class CreateTaxRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str
    description: str
    percentage: Decimal
    id_category: UUID


class UpdateTaxRequest(CreateTaxRequest):
    pass


@router.get("")
async def search(
    handler: Annotated[SearchTaxHandler, Depends(_search_handler)],
    name: str = "",
    description: str = "",
    percentage: Decimal | None = None,
    id_category: Annotated[UUID | None, Query(alias="idCategory")] = None,
    created_at: Annotated[datetime | None, Query(alias="createdAt")] = None,
    updated_at: Annotated[datetime | None, Query(alias="updatedAt")] = None,
    deleted_at: Annotated[datetime | None, Query(alias="deletedAt")] = None,
    order: str | None = None,
    page_index: Annotated[int | None, Query(alias="pageIndex", ge=1)] = None,
    page_size: Annotated[int | None, Query(alias="pageSize", ge=1)] = None,
) -> BaseResultList[object]:
    page, size = paged_search_bounds(page_index, page_size)
    result = await handler.handle(
        SearchTaxQuery(
            name=name,
            description=description,
            percentage=percentage,
            id_category=id_category,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            order=order,
            page_index=page,
            page_size=size,
        )
    )
    return BaseResultList(data=[tax_view(d) for d in result.data], paged_result=paged_view(result))


@router.get("/gridify")
async def search_gridify(
    handler: Annotated[GridifyTaxHandler, Depends(_gridify_handler)],
    filter: str | None = None,  # noqa: A002 - nome do contrato Gridify
    order_by: Annotated[str | None, Query(alias="orderBy")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1)] = 10,
) -> BaseResultList[object]:
    result = await handler.handle(
        GridifyTaxQuery(filter=filter, order_by=order_by, page=page, page_size=page_size)
    )
    return BaseResultList(data=[tax_view(d) for d in result.data], paged_result=paged_view(result))


@router.get("/{tax_id}")
async def get_by_id(
    tax_id: UUID,
    handler: Annotated[GetByIdTaxHandler, Depends(_get_handler)],
) -> BaseResult[object]:
    detailed = await handler.handle(tax_id)
    return BaseResult(data=tax_view(detailed))


@router.post("")
async def create(
    payload: CreateTaxRequest,
    create_handler: Annotated[CreateTaxHandler, Depends(_create_handler)],
    get_handler: Annotated[GetByIdTaxHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[object]:
    tax_id = await create_handler.handle(_to_create(payload))
    detailed = await get_handler.handle(tax_id)
    return BaseResult(data=tax_view(detailed))


@router.put("/{tax_id}")
async def update(
    tax_id: UUID,
    payload: UpdateTaxRequest,
    update_handler: Annotated[UpdateTaxHandler, Depends(_update_handler)],
    get_handler: Annotated[GetByIdTaxHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[object]:
    await update_handler.handle(_to_update(tax_id, payload))
    detailed = await get_handler.handle(tax_id)
    return BaseResult(data=tax_view(detailed))


@router.delete("/{tax_id}")
async def delete(
    tax_id: UUID,
    handler: Annotated[DeleteTaxHandler, Depends(_delete_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> dict[str, object]:
    await handler.handle(DeleteTaxCommand(id=tax_id))
    return {}


def _to_create(payload: CreateTaxRequest) -> CreateTaxCommand:
    return CreateTaxCommand(**payload.model_dump())


def _to_update(tax_id: UUID, payload: UpdateTaxRequest) -> UpdateTaxCommand:
    return UpdateTaxCommand(id=tax_id, **payload.model_dump())
