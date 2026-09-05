"""Resultado paginado genérico das buscas de repositório."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SearchResult[T]:
    data: list[T]
    row_count: int
    page: int
    size: int
