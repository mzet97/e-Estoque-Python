"""Published language: projeções de leitura compartilhadas entre contextos.

Evita dependência entre bounded contexts (Product lê Category/Company via joins
próprios mapeando estes summaries — nunca importa o contexto de origem).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AddressSummary:
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


@dataclass(frozen=True, slots=True)
class CategorySummary:
    id: UUID
    name: str
    description: str
    short_description: str
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None


@dataclass(frozen=True, slots=True)
class CompanySummary:
    id: UUID
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    company_address: AddressSummary
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None


@dataclass(frozen=True, slots=True)
class CustomerSummary:
    id: UUID
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    customer_address: AddressSummary
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None


@dataclass(frozen=True, slots=True)
class ProductSummary:
    id: UUID
    name: str
    description: str
    short_description: str
    image: str
    price: Decimal
    weight: Decimal
    height: Decimal
    length: Decimal
    id_category: UUID
    id_company: UUID
    created_at: datetime
    updated_at: datetime | None
    deleted_at: datetime | None
    category: CategorySummary | None = None
    company: CompanySummary | None = None


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Detailed(Generic[T]):
    """Entity + projeções relacionadas carregadas (equivalente aos Include .NET)."""

    entity: T
    category: CategorySummary | None = None
    company: CompanySummary | None = None
    customer: CustomerSummary | None = None
    product: ProductSummary | None = None
    products: list[ProductSummary] = field(default_factory=list)
