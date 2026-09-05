"""Product: entidade, eventos, critérios e porta de repositório."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID, uuid4

from e_estoque.shared.application.read_models import CompanySummary, Detailed
from e_estoque.shared.domain.checks import (
    audit,
    length,
    positive_decimal,
    provided,
    provided_number,
)
from e_estoque.shared.domain.entity import DomainEvent, Entity, utcnow
from e_estoque.shared.domain.search import SearchResult

EXCHANGE = "product-service"


# ---- Domain Events (payload = wire format .NET) ----
@dataclass(frozen=True, slots=True)
class ProductCreated(DomainEvent):
    # Paridade: o ProductCreated .NET NÃO inclui Image.
    id: UUID
    name: str
    description: str
    short_description: str
    price: Decimal
    weight: Decimal
    height: Decimal
    length: Decimal
    id_category: UUID
    id_company: UUID
    occurred_on: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class ProductUpdated(DomainEvent):
    # Paridade: o handler .NET passa Image ao evento, mas o evento descarta o valor.
    id: UUID
    name: str
    description: str
    short_description: str
    price: Decimal
    weight: Decimal
    height: Decimal
    length: Decimal
    id_category: UUID
    id_company: UUID
    occurred_on: datetime = field(default_factory=utcnow)


# ---- Entity ----
class Product(Entity):
    __slots__ = (
        "name", "description", "short_description", "price", "weight",
        "height", "length", "image", "id_category", "id_company",
    )

    def __init__(
        self,
        id: UUID,  # noqa: A002 - identidade do .NET é "Id"
        name: str,
        description: str,
        short_description: str,
        price: Decimal,
        weight: Decimal,
        height: Decimal,
        length: Decimal,
        image: str,
        id_category: UUID,
        id_company: UUID,
        created_at: datetime,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
        is_deleted: bool = False,
    ) -> None:
        super().__init__(id, created_at, updated_at, deleted_at, is_deleted)
        self.name = name
        self.description = description
        self.short_description = short_description
        self.price = price
        self.weight = weight
        self.height = height
        self.length = length
        self.image = image
        self.id_category = id_category
        self.id_company = id_company

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        short_description: str,
        price: Decimal,
        weight: Decimal,
        height: Decimal,
        length: Decimal,
        image: str,
        id_category: UUID,
        id_company: UUID,
    ) -> "Product":
        product = cls(
            uuid4(), name, description, short_description, price, weight,
            height, length, image, id_category, id_company, utcnow(),
        )
        product.register_event(
            ProductCreated(
                product.id, name, description, short_description, price, weight,
                height, length, id_category, id_company,
            )
        )
        product.validate()
        return product

    @classmethod
    def rehydrate(
        cls,
        id: UUID,  # noqa: A002
        name: str,
        description: str,
        short_description: str,
        price: Decimal,
        weight: Decimal,
        height: Decimal,
        length: Decimal,
        image: str,
        id_category: UUID,
        id_company: UUID,
        created_at: datetime,
        updated_at: datetime | None,
        deleted_at: datetime | None,
        is_deleted: bool,
    ) -> "Product":
        product = cls(
            id, name, description, short_description, price, weight, height,
            length, image, id_category, id_company, created_at,
            updated_at, deleted_at, is_deleted,
        )
        product.validate()
        return product

    def update(
        self,
        name: str,
        description: str,
        short_description: str,
        price: Decimal,
        weight: Decimal,
        height: Decimal,
        length: Decimal,
        image: str,
        id_category: UUID,
        id_company: UUID,
    ) -> None:
        self.name, self.description, self.short_description = name, description, short_description
        self.price, self.weight, self.height, self.length = price, weight, height, length
        self.image, self.id_category, self.id_company = image, id_category, id_company
        self.touch(utcnow())
        self.register_event(
            ProductUpdated(
                self.id, name, description, short_description, price, weight,
                height, length, id_category, id_company,
            )
        )
        self.validate()

    def validate(self) -> None:
        errors: list[str] = []
        audit(self.id, self.created_at, self.updated_at, self.deleted_at, errors)
        provided(errors, self.name, "Name")
        length(errors, self.name, "Name", 3, 250)
        provided(errors, self.description, "Description")
        length(errors, self.description, "Description", 3, 500)
        provided(errors, self.short_description, "ShortDescription")
        length(errors, self.short_description, "ShortDescription", 3, 250)
        provided_number(errors, self.price, "Price")
        positive_decimal(errors, self.price, "Price")
        provided_number(errors, self.height, "Height")
        positive_decimal(errors, self.height, "Height")
        provided_number(errors, self.weight, "Weight")
        positive_decimal(errors, self.weight, "Weight")
        provided_number(errors, self.length, "Length")
        positive_decimal(errors, self.length, "Length")
        provided(errors, self.image, "Image")
        length(errors, self.image, "Image", 3, 5000)
        provided(errors, self.id_category, "IdCategory")
        provided(errors, self.id_company, "IdCompany")
        if errors:
            self.mark_invalid(errors)
        else:
            self.mark_valid()


# ---- Criteria / Port ----
@dataclass(frozen=True, slots=True)
class ProductCriteria:
    """Filtros de igualdade exata do SearchProductQuery (.NET, sem filtro de Image)."""

    id: UUID | None = None
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    price: Decimal | None = None
    weight: Decimal | None = None
    height: Decimal | None = None
    length: Decimal | None = None
    id_category: UUID | None = None
    id_company: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    order: str | None = None
    page: int = 1
    size: int = 10


class CompanyReader(Protocol):
    """Verificação de existência de Company (referencial do Product)."""

    async def exists(self, company_id: UUID) -> bool: ...


class CategoryReader(Protocol):
    """Verificação de existência de Category (referencial do Product)."""

    async def exists(self, category_id: UUID) -> bool: ...


class ProductRepository(Protocol):
    async def save(self, product: Product) -> None: ...

    async def find_by_id(self, product_id: UUID) -> Product | None: ...

    async def find_detailed_by_id(self, product_id: UUID) -> Detailed[Product] | None: ...

    async def search(self, criteria: ProductCriteria) -> SearchResult[Detailed[Product]]: ...

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Detailed[Product]]: ...

    async def delete_hard(self, product_id: UUID) -> None: ...


# CompanySummary reexportado para tipagem dos adapters (contrato de leitura compartilhado).
__all__ = [
    "EXCHANGE",
    "CompanySummary",
    "Detailed",
    "Product",
    "ProductCreated",
    "ProductCriteria",
    "ProductRepository",
    "ProductUpdated",
]
