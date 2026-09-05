"""Envelope de resposta e paginação (contrato JSON .NET: camelCase)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, computed_field
from pydantic.alias_generators import to_camel

from e_estoque.shared.domain.search import SearchResult


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
    def create(cls, current_page: int, page_size: int, row_count: int) -> PagedResult:
        safe_size = max(page_size, 1)
        page_count = -(-row_count // safe_size)
        return cls(
            current_page=current_page,
            page_count=page_count,
            page_size=safe_size,
            row_count=row_count,
        )


class BaseResult[T](BaseModel):
    """Envelope de item único: {"data": T, "success": true, "message": ""} (camelCase)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data: T | None = None
    success: bool = True
    message: str = ""


class BaseResultList[T](BaseModel):
    """Envelope de listas: {"data": [...], "pagedResult": {...}, ...}."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data: list[T] = []
    paged_result: PagedResult | None = None
    success: bool = True
    message: str = ""


def paged_view[T](result: SearchResult[T]) -> PagedResult:
    """PagedResult do contrato a partir de um SearchResult de repositório."""
    return PagedResult.create(result.page, result.size, result.row_count)


def paged_search_bounds(page_index: int | None, page_size: int | None) -> tuple[int, int]:
    """Defaults do .NET: pageIndex 1, pageSize 10 (sem teto — paridade).

    Valores inválidos (< 1) violam o contrato de paginação → ValidationError (400),
    em vez do ArgumentOutOfRangeException→500 do .NET (BUG-FIX documentado).
    """
    from e_estoque.shared.domain.errors import ValidationError

    if page_index is not None and page_index < 1:
        raise ValidationError("Page index must be greater or equal to 1")
    if page_size is not None and page_size < 1:
        raise ValidationError("Page size must be greater or equal to 1")
    page = page_index if page_index is not None else 1
    size = page_size if page_size is not None else 10
    return page, size
