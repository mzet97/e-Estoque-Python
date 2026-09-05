"""Router de Inventory — contrato .NET: `api/Inventories` (POST → 200)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from e_estoque.inventory.application.inventory_handlers import (
    CreateInventoryCommand,
    CreateInventoryHandler,
    DeleteInventoryCommand,
    DeleteInventoryHandler,
    GetByIdInventoryHandler,
    GridifyInventoryHandler,
    GridifyInventoryQuery,
    SearchInventoryHandler,
    SearchInventoryQuery,
    UpdateInventoryCommand,
    UpdateInventoryHandler,
)
from e_estoque.inventory.domain.inventory import InventoryRepository, ProductReader
from e_estoque.inventory.infrastructure.inventory_repository import SqlInventoryRepository
from e_estoque.product.infrastructure.product_repository import SqlProductRepository
from e_estoque.shared.api.schemas import (
    BaseResult,
    BaseResultList,
    paged_search_bounds,
    paged_view,
)
from e_estoque.shared.api.security import CurrentUser, current_user, require_create
from e_estoque.shared.api.views import inventory_view
from e_estoque.shared.application.message_bus import MessageBus
from e_estoque.shared.infrastructure.db import UnitOfWork, open_uow

router = APIRouter(
    prefix="/api/Inventories", tags=["Inventories"], dependencies=[Depends(current_user)]
)


def _repository(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> InventoryRepository:
    return SqlInventoryRepository(uow.session)


def _bus(request: Request) -> MessageBus:
    bus: MessageBus = request.app.state.bus
    return bus


def _product_reader(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> ProductReader:
    return SqlProductRepository(uow.session)


def _search_handler(
    repository: Annotated[InventoryRepository, Depends(_repository)],
) -> SearchInventoryHandler:
    return SearchInventoryHandler(repository)


def _gridify_handler(
    repository: Annotated[InventoryRepository, Depends(_repository)],
) -> GridifyInventoryHandler:
    return GridifyInventoryHandler(repository)


def _get_handler(
    repository: Annotated[InventoryRepository, Depends(_repository)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> GetByIdInventoryHandler:
    return GetByIdInventoryHandler(repository, bus)


def _create_handler(
    repository: Annotated[InventoryRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
    product_reader: Annotated[ProductReader, Depends(_product_reader)],
) -> CreateInventoryHandler:
    return CreateInventoryHandler(repository, uow, bus, product_reader)


def _update_handler(
    repository: Annotated[InventoryRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
    product_reader: Annotated[ProductReader, Depends(_product_reader)],
) -> UpdateInventoryHandler:
    return UpdateInventoryHandler(repository, uow, bus, product_reader)


def _delete_handler(
    repository: Annotated[InventoryRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> DeleteInventoryHandler:
    return DeleteInventoryHandler(repository, uow, bus)


class CreateInventoryRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    quantity: int
    date_order: datetime
    id_product: UUID


class UpdateInventoryRequest(CreateInventoryRequest):
    pass


@router.get("")
async def search(
    handler: Annotated[SearchInventoryHandler, Depends(_search_handler)],
    quantity: int | None = None,
    date_order: Annotated[datetime | None, Query(alias="dateOrder")] = None,
    id_product: Annotated[UUID | None, Query(alias="idProduct")] = None,
    id: UUID | None = None,
    created_at: Annotated[datetime | None, Query(alias="createdAt")] = None,
    updated_at: Annotated[datetime | None, Query(alias="updatedAt")] = None,
    deleted_at: Annotated[datetime | None, Query(alias="deletedAt")] = None,
    order: str | None = None,
    page_index: Annotated[int | None, Query(alias="pageIndex", ge=1)] = None,
    page_size: Annotated[int | None, Query(alias="pageSize", ge=1)] = None,
) -> BaseResultList[object]:
    page, size = paged_search_bounds(page_index, page_size)
    result = await handler.handle(
        SearchInventoryQuery(
            quantity=quantity,
            date_order=date_order,
            id_product=id_product,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            order=order,
            page_index=page,
            page_size=size,
        )
    )
    return BaseResultList(
        data=[inventory_view(d) for d in result.data],
        paged_result=paged_view(result),
    )


@router.get("/gridify")
async def search_gridify(
    handler: Annotated[GridifyInventoryHandler, Depends(_gridify_handler)],
    filter: str | None = None,  # noqa: A002 - nome do contrato Gridify
    order_by: Annotated[str | None, Query(alias="orderBy")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1)] = 10,
) -> BaseResultList[object]:
    result = await handler.handle(
        GridifyInventoryQuery(filter=filter, order_by=order_by, page=page, page_size=page_size)
    )
    return BaseResultList(
        data=[inventory_view(d) for d in result.data],
        paged_result=paged_view(result),
    )


@router.get("/{inventory_id}")
async def get_by_id(
    inventory_id: UUID,
    handler: Annotated[GetByIdInventoryHandler, Depends(_get_handler)],
) -> BaseResult[object]:
    detailed = await handler.handle(inventory_id)
    return BaseResult(data=inventory_view(detailed))


@router.post("")
async def create(
    payload: CreateInventoryRequest,
    create_handler: Annotated[CreateInventoryHandler, Depends(_create_handler)],
    get_handler: Annotated[GetByIdInventoryHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[object]:
    inventory_id = await create_handler.handle(_to_create(payload))
    detailed = await get_handler.handle(inventory_id)
    return BaseResult(data=inventory_view(detailed))


@router.put("/{inventory_id}")
async def update(
    inventory_id: UUID,
    payload: UpdateInventoryRequest,
    update_handler: Annotated[UpdateInventoryHandler, Depends(_update_handler)],
    get_handler: Annotated[GetByIdInventoryHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[object]:
    await update_handler.handle(_to_update(inventory_id, payload))
    detailed = await get_handler.handle(inventory_id)
    return BaseResult(data=inventory_view(detailed))


@router.delete("/{inventory_id}")
async def delete(
    inventory_id: UUID,
    handler: Annotated[DeleteInventoryHandler, Depends(_delete_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> dict[str, object]:
    await handler.handle(DeleteInventoryCommand(id=inventory_id))
    return {}


def _to_create(payload: CreateInventoryRequest) -> CreateInventoryCommand:
    return CreateInventoryCommand(**payload.model_dump())


def _to_update(inventory_id: UUID, payload: UpdateInventoryRequest) -> UpdateInventoryCommand:
    return UpdateInventoryCommand(id=inventory_id, **payload.model_dump())
