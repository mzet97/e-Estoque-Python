"""Envelope de resposta e paginação (contrato JSON .NET: camelCase)."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, computed_field
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class _Camel(BaseModel):
    """Base com serialização camelCase (contrato .NET)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PagedResult(_Camel):
    """Equivalente ao PagedResult .NET, incluindo campos calculados."""

    current_page: int
    page_count: int
    page_size: int
    row_count: int

    @property
    def skip(self) -> int:
        return (self.current_page - 1) * self.page_size

    @computed_field  # type: ignore[prop-decorator]
    @property
    def first_row_on_page(self) -> int:
        return (self.current_page - 1) * self.page_size + 1

    @computed_field  # type: ignore[prop-decorator]
    @property
    def last_row_on_page(self) -> int:
        return min(self.current_page * self.page_size, self.row_count)

    @classmethod
    def create(cls, current_page: int, page_size: int, row_count: int) -> "PagedResult":
        safe_size = max(page_size, 1)
        page_count = -(-row_count // safe_size)
        return cls(
            current_page=current_page,
            page_count=page_count,
            page_size=safe_size,
            row_count=row_count,
        )


class BaseResult(_Camel, Generic[T]):
    """Envelope de item único: {"data": T, "success": true, "message": ""}."""

    data: T | None = None
    success: bool = True
    message: str = ""


class BaseResultList(_Camel, Generic[T]):
    """Envelope de listas: {"data": [...], "pagedResult": {...}, ...}."""

    data: list[T] = []
    paged_result: PagedResult | None = None
    success: bool = True
    message: str = ""


def paged_search_bounds(page_index: int | None, page_size: int | None) -> tuple[int, int]:
    """Defaults do .NET: pageIndex 1, pageSize 10, cap 1000."""
    page = page_index if page_index and page_index >= 1 else 1
    size = page_size if page_size and page_size >= 1 else 10
    return page, min(size, 1000)
