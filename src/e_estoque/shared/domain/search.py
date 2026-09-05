"""Resultado paginado genérico das buscas de repositório."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class SearchResult(Generic[T]):
    data: list[T]
    row_count: int
    page: int
    size: int
