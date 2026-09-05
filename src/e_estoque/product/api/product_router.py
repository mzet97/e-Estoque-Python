"""Router de Product — contrato .NET: `api/Products` (POST → 200)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from e_estoque.product.application.product_handlers import (
    CreateProductCommand,
    CreateProductHandler,
    DeleteProductCommand,
    DeleteProductHandler,
    GetByIdProductHandler,
    GridifyProductHandler,
    GridifyProductQuery,
    SearchProductHandler,
    SearchProductQuery,
    UpdateProductCommand,
    UpdateProductHandler,
)
from e_estoque.company.infrastructure.company_repository import SqlCompanyRepository
from e_estoque.product.domain.product import (
    CategoryReader,
    CompanyReader,
    ProductRepository,
)
from e_estoque.product.infrastructure.category_repository import SqlCategoryRepository
from e_estoque.product.infrastructure.product_repository import SqlProductRepository
from e_estoque.shared.api.schemas import (
    BaseResult,
    BaseResultList,
    paged_search_bounds,
    paged_view,
)
from e_estoque.shared.api.security import CurrentUser, require_create
from e_estoque.shared.api.views import product_view
from e_estoque.shared.application.message_bus import MessageBus
from e_estoque.shared.infrastructure.db import UnitOfWork, open_uow

router = APIRouter(prefix="/api/Products", tags=["Products"])


def _repository(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> ProductRepository:
    return SqlProductRepository(uow.session)


def _bus(request: Request) -> MessageBus:
    bus: MessageBus = request.app.state.bus
    return bus


def _category_reader_dep(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> CategoryReader:
    return SqlCategoryRepository(uow.session)


def _company_reader_dep(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> CompanyReader:
    return SqlCompanyRepository(uow.session)


def _search_handler(
    repository: Annotated[ProductRepository, Depends(_repository)],
) -> SearchProductHandler:
    return SearchProductHandler(repository)


def _gridify_handler(
    repository: Annotated[ProductRepository, Depends(_repository)],
) -> GridifyProductHandler:
    return GridifyProductHandler(repository)


def _get_handler(
    repository: Annotated[ProductRepository, Depends(_repository)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> GetByIdProductHandler:
    return GetByIdProductHandler(repository, bus)


def _create_handler(
    repository: Annotated[ProductRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
    category_reader: Annotated[CategoryReader, Depends(_category_reader_dep)],
    company_reader: Annotated[CompanyReader, Depends(_company_reader_dep)],
) -> CreateProductHandler:
    return CreateProductHandler(repository, uow, bus, category_reader, company_reader)


def _update_handler(
    repository: Annotated[ProductRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
    category_reader: Annotated[CategoryReader, Depends(_category_reader_dep)],
    company_reader: Annotated[CompanyReader, Depends(_company_reader_dep)],
) -> UpdateProductHandler:
    return UpdateProductHandler(repository, uow, bus, category_reader, company_reader)


def _delete_handler(
    repository: Annotated[ProductRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> DeleteProductHandler:
    return DeleteProductHandler(repository, uow, bus)


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

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


class UpdateProductRequest(CreateProductRequest):
    pass


@router.get("")
async def search(
    handler: Annotated[SearchProductHandler, Depends(_search_handler)],
    name: str = "",
    description: str = "",
    short_description: Annotated[str, Query(alias="shortDescription")] = "",
    price: Decimal | None = None,
    weight: Decimal | None = None,
    height: Decimal | None = None,
    length: Decimal | None = None,
    id_category: Annotated[UUID | None, Query(alias="idCategory")] = None,
    id_company: Annotated[UUID | None, Query(alias="idCompany")] = None,
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
        SearchProductQuery(
            name=name, description=description, short_description=short_description,
            price=price, weight=weight, height=height, length=length,
            id_category=id_category, id_company=id_company, id=id,
            created_at=created_at, updated_at=updated_at, deleted_at=deleted_at,
            order=order, page_index=page, page_size=size,
        )
    )
    return BaseResultList(
        data=[product_view(d) for d in result.data],  # type: ignore[arg-type]
        paged_result=paged_view(result),
    )


@router.get("/gridify")
async def search_gridify(
    handler: Annotated[GridifyProductHandler, Depends(_gridify_handler)],
    filter: str | None = None,  # noqa: A002 - nome do contrato Gridify
    order_by: Annotated[str | None, Query(alias="orderBy")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1)] = 10,
) -> BaseResultList[object]:
    result = await handler.handle(
        GridifyProductQuery(filter=filter, order_by=order_by, page=page, page_size=page_size)
    )
    return BaseResultList(
        data=[product_view(d) for d in result.data],
        paged_result=paged_view(result),
    )


@router.get("/{product_id}")
async def get_by_id(
    product_id: UUID,
    handler: Annotated[GetByIdProductHandler, Depends(_get_handler)],
) -> BaseResult[object]:
    detailed = await handler.handle(product_id)
    return BaseResult(data=product_view(detailed))


@router.post("")
async def create(
    payload: CreateProductRequest,
    create_handler: Annotated[CreateProductHandler, Depends(_create_handler)],
    get_handler: Annotated[GetByIdProductHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[object]:
    product_id = await create_handler.handle(_to_command(payload))
    detailed = await get_handler.handle(product_id)
    return BaseResult(data=product_view(detailed))


@router.put("/{product_id}")
async def update(
    product_id: UUID,
    payload: UpdateProductRequest,
    update_handler: Annotated[UpdateProductHandler, Depends(_update_handler)],
    get_handler: Annotated[GetByIdProductHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[object]:
    await update_handler.handle(_to_command(payload, product_id))
    detailed = await get_handler.handle(product_id)
    return BaseResult(data=product_view(detailed))


@router.delete("/{product_id}")
async def delete(
    product_id: UUID,
    handler: Annotated[DeleteProductHandler, Depends(_delete_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> dict[str, object]:
    await handler.handle(DeleteProductCommand(id=product_id))
    return {}


def _to_command(
    payload: CreateProductRequest, product_id: UUID | None = None
) -> CreateProductCommand | UpdateProductCommand:
    data = payload.model_dump()
    if product_id is None:
        return CreateProductCommand(**data)
    return UpdateProductCommand(id=product_id, **data)
