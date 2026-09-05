"""Router de Sale — contrato .NET: `api/Sales` (delete soft, POST → 200)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from e_estoque.customer.infrastructure.customer_repository import SqlCustomerRepository
from e_estoque.product.infrastructure.product_repository import SqlProductRepository
from e_estoque.sale.application.sale_handlers import (
    CreateSaleCommand,
    CreateSaleHandler,
    DeleteSaleCommand,
    DeleteSaleHandler,
    GetByIdSaleHandler,
    GridifySaleHandler,
    GridifySaleQuery,
    SearchSaleHandler,
    SearchSaleQuery,
    UpdateSaleCommand,
    UpdateSaleHandler,
)
from e_estoque.sale.domain.sale import CustomerReader, ProductReader, SaleRepository
from e_estoque.sale.infrastructure.sale_repository import SqlSaleRepository
from e_estoque.shared.api.schemas import (
    BaseResult,
    BaseResultList,
    paged_search_bounds,
    paged_view,
)
from e_estoque.shared.api.security import CurrentUser, current_user, require_create
from e_estoque.shared.api.views import sale_view
from e_estoque.shared.application.message_bus import MessageBus
from e_estoque.shared.infrastructure.db import UnitOfWork, open_uow

router = APIRouter(prefix="/api/Sales", tags=["Sales"], dependencies=[Depends(current_user)])


def _repository(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> SaleRepository:
    return SqlSaleRepository(uow.session)


def _bus(request: Request) -> MessageBus:
    bus: MessageBus = request.app.state.bus
    return bus


def _customer_reader(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> CustomerReader:
    return SqlCustomerRepository(uow.session)


def _product_reader(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> ProductReader:
    return SqlProductRepository(uow.session)


def _search_handler(
    repository: Annotated[SaleRepository, Depends(_repository)],
) -> SearchSaleHandler:
    return SearchSaleHandler(repository)


def _gridify_handler(
    repository: Annotated[SaleRepository, Depends(_repository)],
) -> GridifySaleHandler:
    return GridifySaleHandler(repository)


def _get_handler(
    repository: Annotated[SaleRepository, Depends(_repository)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> GetByIdSaleHandler:
    return GetByIdSaleHandler(repository, bus)


def _create_handler(
    repository: Annotated[SaleRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
    customer_reader: Annotated[CustomerReader, Depends(_customer_reader)],
    product_reader: Annotated[ProductReader, Depends(_product_reader)],
) -> CreateSaleHandler:
    return CreateSaleHandler(repository, uow, bus, customer_reader, product_reader)


def _update_handler(
    repository: Annotated[SaleRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
    customer_reader: Annotated[CustomerReader, Depends(_customer_reader)],
    product_reader: Annotated[ProductReader, Depends(_product_reader)],
) -> UpdateSaleHandler:
    return UpdateSaleHandler(repository, uow, bus, customer_reader, product_reader)


def _delete_handler(
    repository: Annotated[SaleRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> DeleteSaleHandler:
    return DeleteSaleHandler(repository, uow, bus)


class CreateSaleRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    quantity: int
    total_price: Decimal
    total_tax: Decimal
    sale_type: Annotated[int, Field(ge=1, le=2)]
    payment_type: Annotated[int, Field(ge=1, le=4)]
    delivery_date: datetime | None = None
    sale_date: datetime
    payment_date: datetime | None = None
    id_customer: UUID
    ids_products: list[UUID]


class UpdateSaleRequest(CreateSaleRequest):
    pass


@router.get("")
async def search(
    handler: Annotated[SearchSaleHandler, Depends(_search_handler)],
    quantity: int | None = None,
    total_price: Annotated[Decimal | None, Query(alias="totalPrice")] = None,
    total_tax: Annotated[Decimal | None, Query(alias="totalTax")] = None,
    sale_type: Annotated[str, Query(alias="saleType")] = "",
    payment_type: Annotated[str, Query(alias="paymentType")] = "",
    delivery_date: Annotated[datetime | None, Query(alias="deliveryDate")] = None,
    sale_date: Annotated[datetime | None, Query(alias="saleDate")] = None,
    payment_date: Annotated[datetime | None, Query(alias="paymentDate")] = None,
    id_product: Annotated[UUID | None, Query(alias="idProduct")] = None,
    id_customer: Annotated[UUID | None, Query(alias="idCustomer")] = None,
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
        SearchSaleQuery(
            quantity=quantity,
            total_price=total_price,
            total_tax=total_tax,
            sale_type=sale_type,
            payment_type=payment_type,
            delivery_date=delivery_date,
            sale_date=sale_date,
            payment_date=payment_date,
            id_product=id_product,
            id_customer=id_customer,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            order=order,
            page_index=page,
            page_size=size,
        )
    )
    return BaseResultList(data=[sale_view(d) for d in result.data], paged_result=paged_view(result))


@router.get("/gridify")
async def search_gridify(
    handler: Annotated[GridifySaleHandler, Depends(_gridify_handler)],
    filter: str | None = None,  # noqa: A002 - nome do contrato Gridify
    order_by: Annotated[str | None, Query(alias="orderBy")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1)] = 10,
) -> BaseResultList[object]:
    result = await handler.handle(
        GridifySaleQuery(filter=filter, order_by=order_by, page=page, page_size=page_size)
    )
    return BaseResultList(data=[sale_view(d) for d in result.data], paged_result=paged_view(result))


@router.get("/{sale_id}")
async def get_by_id(
    sale_id: UUID,
    handler: Annotated[GetByIdSaleHandler, Depends(_get_handler)],
) -> BaseResult[object]:
    detailed = await handler.handle(sale_id)
    return BaseResult(data=sale_view(detailed))


@router.post("")
async def create(
    payload: CreateSaleRequest,
    create_handler: Annotated[CreateSaleHandler, Depends(_create_handler)],
    get_handler: Annotated[GetByIdSaleHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[object]:
    sale_id = await create_handler.handle(_to_create(payload))
    detailed = await get_handler.handle(sale_id)
    return BaseResult(data=sale_view(detailed))


@router.put("/{sale_id}")
async def update(
    sale_id: UUID,
    payload: UpdateSaleRequest,
    update_handler: Annotated[UpdateSaleHandler, Depends(_update_handler)],
    get_handler: Annotated[GetByIdSaleHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[object]:
    await update_handler.handle(_to_update(sale_id, payload))
    detailed = await get_handler.handle(sale_id)
    return BaseResult(data=sale_view(detailed))


@router.delete("/{sale_id}")
async def delete(
    sale_id: UUID,
    handler: Annotated[DeleteSaleHandler, Depends(_delete_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> dict[str, object]:
    await handler.handle(DeleteSaleCommand(id=sale_id))
    return {}


def _to_create(payload: CreateSaleRequest) -> CreateSaleCommand:
    # Datas nulas seguem ao domínio: SaleValidation exige deliveryDate/paymentDate.
    return CreateSaleCommand(**payload.model_dump())


def _to_update(sale_id: UUID, payload: UpdateSaleRequest) -> UpdateSaleCommand:
    return UpdateSaleCommand(id=sale_id, **payload.model_dump())
