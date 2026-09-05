"""Router de Category — contrato .NET: `api/Categories`.

Paridades: POST → 201 + Location; PUT/DELETE → 200 (DELETE corpo `{}`).
Leitura: autenticado. Escrita: role `Create`.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from e_estoque.product.application.category_handlers import (
    CreateCategoryCommand,
    CreateCategoryHandler,
    DeleteCategoryCommand,
    DeleteCategoryHandler,
    GetByIdCategoryHandler,
    GridifyCategoryHandler,
    GridifyCategoryQuery,
    SearchCategoryHandler,
    SearchCategoryQuery,
    UpdateCategoryCommand,
    UpdateCategoryHandler,
)
from e_estoque.product.domain.category import CategoryRepository
from e_estoque.product.infrastructure.category_repository import SqlCategoryRepository
from e_estoque.shared.api.schemas import (
    BaseResult,
    BaseResultList,
    paged_search_bounds,
    paged_view,
)
from e_estoque.shared.api.security import CurrentUser, require_create
from e_estoque.shared.api.views import CategoryView
from e_estoque.shared.application.message_bus import MessageBus
from e_estoque.shared.infrastructure.db import UnitOfWork, open_uow

router = APIRouter(prefix="/api/Categories", tags=["Categories"])


# ---- dependências ----
def _repository(uow: Annotated[UnitOfWork, Depends(open_uow)]) -> CategoryRepository:
    return SqlCategoryRepository(uow.session)


def _bus(request: Request) -> MessageBus:
    bus: MessageBus = request.app.state.bus
    return bus


def _search_handler(
    repository: Annotated[CategoryRepository, Depends(_repository)],
) -> SearchCategoryHandler:
    return SearchCategoryHandler(repository)


def _gridify_handler(
    repository: Annotated[CategoryRepository, Depends(_repository)],
) -> GridifyCategoryHandler:
    return GridifyCategoryHandler(repository)


def _get_handler(
    repository: Annotated[CategoryRepository, Depends(_repository)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> GetByIdCategoryHandler:
    return GetByIdCategoryHandler(repository, bus)


def _create_handler(
    repository: Annotated[CategoryRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> CreateCategoryHandler:
    return CreateCategoryHandler(repository, uow, bus)


def _update_handler(
    repository: Annotated[CategoryRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> UpdateCategoryHandler:
    return UpdateCategoryHandler(repository, uow, bus)


def _delete_handler(
    repository: Annotated[CategoryRepository, Depends(_repository)],
    uow: Annotated[UnitOfWork, Depends(open_uow)],
    bus: Annotated[MessageBus, Depends(_bus)],
) -> DeleteCategoryHandler:
    return DeleteCategoryHandler(repository, uow, bus)


# ---- request bodies (entrada camelCase case-insensitive como no .NET) ----
class CreateCategoryRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str
    description: str
    short_description: str


class UpdateCategoryRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str
    description: str
    short_description: str


# ---- endpoints ----
@router.get("")
async def search(
    handler: Annotated[SearchCategoryHandler, Depends(_search_handler)],
    name: str = "",
    description: str = "",
    short_description: Annotated[str, Query(alias="shortDescription")] = "",
    id: UUID | None = None,
    created_at: Annotated[datetime | None, Query(alias="createdAt")] = None,
    updated_at: Annotated[datetime | None, Query(alias="updatedAt")] = None,
    deleted_at: Annotated[datetime | None, Query(alias="deletedAt")] = None,
    order: str | None = None,
    page_index: Annotated[int | None, Query(alias="pageIndex", ge=1)] = None,
    page_size: Annotated[int | None, Query(alias="pageSize", ge=1)] = None,
) -> BaseResultList[CategoryView]:
    page, size = paged_search_bounds(page_index, page_size)
    result = await handler.handle(
        SearchCategoryQuery(
            name=name,
            description=description,
            short_description=short_description,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            order=order,
            page_index=page,
            page_size=size,
        )
    )
    return BaseResultList[CategoryView](
        data=[CategoryView.model_validate(c, from_attributes=True) for c in result.data],
        paged_result=paged_view(result),
    )


@router.get("/gridify")
async def search_gridify(
    handler: Annotated[GridifyCategoryHandler, Depends(_gridify_handler)],
    filter: str | None = None,  # noqa: A002 - nome do contrato Gridify
    order_by: Annotated[str | None, Query(alias="orderBy")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1)] = 10,
) -> BaseResultList[CategoryView]:
    result = await handler.handle(
        GridifyCategoryQuery(filter=filter, order_by=order_by, page=page, page_size=page_size)
    )
    return BaseResultList[CategoryView](
        data=[CategoryView.model_validate(c, from_attributes=True) for c in result.data],
        paged_result=paged_view(result),
    )


@router.get("/{category_id}")
async def get_by_id(
    category_id: UUID,
    handler: Annotated[GetByIdCategoryHandler, Depends(_get_handler)],
) -> BaseResult[CategoryView]:
    category = await handler.handle(category_id)
    return BaseResult[CategoryView](
        data=CategoryView.model_validate(category, from_attributes=True)
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create(
    payload: CreateCategoryRequest,
    response: Response,
    create_handler: Annotated[CreateCategoryHandler, Depends(_create_handler)],
    get_handler: Annotated[GetByIdCategoryHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[CategoryView]:
    """Paridade .NET: único POST do sistema com 201 CreatedAtAction + Location."""
    category_id = await create_handler.handle(
        CreateCategoryCommand(
            name=payload.name,
            description=payload.description,
            short_description=payload.short_description,
        )
    )
    response.headers["Location"] = f"/api/Categories/{category_id}"
    category = await get_handler.handle(category_id)
    return BaseResult[CategoryView](
        data=CategoryView.model_validate(category, from_attributes=True)
    )


@router.put("/{category_id}")
async def update(
    category_id: UUID,
    payload: UpdateCategoryRequest,
    update_handler: Annotated[UpdateCategoryHandler, Depends(_update_handler)],
    get_handler: Annotated[GetByIdCategoryHandler, Depends(_get_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> BaseResult[CategoryView]:
    await update_handler.handle(
        UpdateCategoryCommand(
            id=category_id,
            name=payload.name,
            description=payload.description,
            short_description=payload.short_description,
        )
    )
    category = await get_handler.handle(category_id)
    return BaseResult[CategoryView](
        data=CategoryView.model_validate(category, from_attributes=True)
    )


@router.delete("/{category_id}")
async def delete(
    category_id: UUID,
    handler: Annotated[DeleteCategoryHandler, Depends(_delete_handler)],
    _user: Annotated[CurrentUser, Depends(require_create)],
) -> dict[str, object]:
    """Paridade .NET: CustomResponse(true, Unit) → 200 com corpo `{}`."""
    await handler.handle(DeleteCategoryCommand(id=category_id))
    return {}
