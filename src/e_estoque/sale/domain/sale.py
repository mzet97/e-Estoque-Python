"""Sales: enums, entidades Sale/SaleProduct, eventos, critérios e porta de repositório."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import IntEnum
from typing import Protocol
from uuid import UUID, uuid4

from e_estoque.shared.application.read_models import Detailed
from e_estoque.shared.domain.checks import (
    audit,
    positive,
    provided,
    provided_number,
    when,
)
from e_estoque.shared.domain.entity import DomainEvent, Entity, utcnow
from e_estoque.shared.domain.search import SearchResult

EXCHANGE = "sale-service"


# ---- Enums (helpers .NET preservados, incluindo o fallback no parse inválido) ----
class SaleType(IntEnum):
    UNITARY = 1
    RECURRENT = 2

    @classmethod
    def from_string(cls, value: str) -> SaleType:
        """FromString .NET (TryParse case-insensitive); fallback UNITARY."""
        key = value.strip().replace("_", "").replace(" ", "").upper()
        for member in cls:
            if member.name.upper() == key:
                return member
        return cls.UNITARY


class PaymentType(IntEnum):
    PIX = 1
    DEPOSIT = 2
    CREDIT_CARD = 3
    DEBIT_CARD = 4

    @classmethod
    def from_string(cls, value: str) -> PaymentType:
        """FromString .NET (TryParse case-insensitive); fallback PIX."""
        key = value.strip().replace("_", "").replace(" ", "").upper()
        for member in cls:
            if member.name.upper().replace("_", "") == key:
                return member
        return cls.PIX


# ---- Domain Events ----
@dataclass(frozen=True, slots=True)
class SaleCreated(DomainEvent):
    id: UUID
    quantity: int
    total_price: Decimal
    total_tax: Decimal
    sale_type: SaleType
    payment_type: PaymentType
    delivery_date: datetime | None
    sale_date: datetime
    payment_date: datetime | None
    id_customer: UUID
    products: list[SaleProduct]
    occurred_on: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class SaleUpdated(DomainEvent):
    id: UUID
    quantity: int
    total_price: Decimal
    total_tax: Decimal
    sale_type: SaleType
    payment_type: PaymentType
    delivery_date: datetime | None
    sale_date: datetime
    payment_date: datetime | None
    id_customer: UUID
    products: list[SaleProduct]
    occurred_on: datetime = field(default_factory=utcnow)


# ---- Entities ----
class SaleProduct(Entity):
    """Linha de venda (1 por produto, com a quantidade da venda — paridade .NET)."""

    __slots__ = ("quantity", "id_product", "id_sale")

    def __init__(
        self,
        id: UUID,  # noqa: A002
        quantity: int,
        id_product: UUID,
        id_sale: UUID,
        created_at: datetime,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
        is_deleted: bool = False,
    ) -> None:
        super().__init__(id, created_at, updated_at, deleted_at, is_deleted)
        self.quantity = quantity
        self.id_product = id_product
        self.id_sale = id_sale

    @classmethod
    def create(cls, quantity: int, id_product: UUID, id_sale: UUID) -> SaleProduct:
        return cls(uuid4(), quantity, id_product, id_sale, utcnow())

    def validate(self) -> None:
        """SaleProductValidation .NET: sem EntityValidation e sem regra de Quantity."""
        errors: list[str] = []
        when(self.id_product is None, "The IdProduct cannot be empty.", errors)
        when(self.id_sale is None, "The IdSale cannot be empty.", errors)
        if errors:
            self.mark_invalid(errors)
        else:
            self.mark_valid()


class Sale(Entity):
    __slots__ = (
        "quantity",
        "total_price",
        "total_tax",
        "sale_type",
        "payment_type",
        "delivery_date",
        "sale_date",
        "payment_date",
        "id_customer",
        "sale_products",
    )

    def __init__(
        self,
        id: UUID,  # noqa: A002
        quantity: int,
        total_price: Decimal,
        total_tax: Decimal,
        sale_type: SaleType,
        payment_type: PaymentType,
        delivery_date: datetime | None,
        sale_date: datetime,
        payment_date: datetime | None,
        id_customer: UUID,
        sale_products: list[SaleProduct],
        created_at: datetime,
        updated_at: datetime | None = None,
        deleted_at: datetime | None = None,
        is_deleted: bool = False,
    ) -> None:
        super().__init__(id, created_at, updated_at, deleted_at, is_deleted)
        self.quantity = quantity
        self.total_price = total_price
        self.total_tax = total_tax
        self.sale_type = sale_type
        self.payment_type = payment_type
        self.delivery_date = delivery_date
        self.sale_date = sale_date
        self.payment_date = payment_date
        self.id_customer = id_customer
        self.sale_products = sale_products

    @classmethod
    def create(
        cls,
        quantity: int,
        total_price: Decimal,
        total_tax: Decimal,
        sale_type: SaleType,
        payment_type: PaymentType,
        delivery_date: datetime | None,
        sale_date: datetime,
        payment_date: datetime | None,
        id_customer: UUID,
        ids_products: list[UUID],
    ) -> Sale:
        sale = cls(
            uuid4(),
            quantity,
            total_price,
            total_tax,
            sale_type,
            payment_type,
            delivery_date,
            sale_date,
            payment_date,
            id_customer,
            [SaleProduct.create(quantity, pid, uuid4()) for pid in ids_products],
            utcnow(),
        )
        for line in sale.sale_products:
            line.id_sale = sale.id
        sale.register_event(
            SaleCreated(
                sale.id,
                quantity,
                total_price,
                total_tax,
                sale_type,
                payment_type,
                delivery_date,
                sale_date,
                payment_date,
                id_customer,
                sale.sale_products,
            )
        )
        sale.validate()
        return sale

    @classmethod
    def rehydrate(
        cls,
        id: UUID,  # noqa: A002
        quantity: int,
        total_price: Decimal,
        total_tax: Decimal,
        sale_type: SaleType,
        payment_type: PaymentType,
        delivery_date: datetime | None,
        sale_date: datetime,
        payment_date: datetime | None,
        id_customer: UUID,
        sale_products: list[SaleProduct],
        created_at: datetime,
        updated_at: datetime | None,
        deleted_at: datetime | None,
        is_deleted: bool,
    ) -> Sale:
        sale = cls(
            id,
            quantity,
            total_price,
            total_tax,
            sale_type,
            payment_type,
            delivery_date,
            sale_date,
            payment_date,
            id_customer,
            sale_products,
            created_at,
            updated_at,
            deleted_at,
            is_deleted,
        )
        sale.validate()
        return sale

    def update(
        self,
        quantity: int,
        total_price: Decimal,
        total_tax: Decimal,
        sale_type: SaleType,
        payment_type: PaymentType,
        delivery_date: datetime | None,
        sale_date: datetime,
        payment_date: datetime | None,
        id_customer: UUID,
        ids_products: list[UUID],
    ) -> None:
        self.quantity = quantity
        self.total_price = total_price
        self.total_tax = total_tax
        self.sale_type = sale_type
        self.payment_type = payment_type
        self.delivery_date = delivery_date
        self.sale_date = sale_date
        self.payment_date = payment_date
        self.id_customer = id_customer
        self.sale_products = [SaleProduct.create(quantity, pid, self.id) for pid in ids_products]
        self.touch(utcnow())
        self.register_event(
            SaleUpdated(
                self.id,
                quantity,
                total_price,
                total_tax,
                sale_type,
                payment_type,
                delivery_date,
                sale_date,
                payment_date,
                id_customer,
                self.sale_products,
            )
        )
        self.validate()

    def validate(self) -> None:
        """SaleValidation .NET: total_tax=0 é inválido; datas opcionais obrigatórias (paridade)."""
        errors: list[str] = []
        audit(self.id, self.created_at, self.updated_at, self.deleted_at, errors)
        provided_number(errors, self.quantity, "Quantity")
        positive(errors, self.quantity, "Quantity")
        provided_number(errors, self.sale_type, "SaleType")
        provided_number(errors, self.payment_type, "PaymentType")
        provided_number(errors, self.total_price, "TotalPrice")
        when(
            self.total_price is not None and self.total_price <= 0,
            "The TotalPrice needs to be greater than 0",
            errors,
        )
        provided_number(errors, self.total_tax, "TotalTax")
        when(
            self.total_tax is not None and self.total_tax <= 0,
            "The TotalTax needs to be greater than 0",
            errors,
        )
        provided(errors, self.delivery_date, "DeliveryDate")
        provided(errors, self.sale_date, "SaleDate")
        provided(errors, self.payment_date, "PaymentDate")
        provided(errors, self.id_customer, "IdCustomer")
        if errors:
            self.mark_invalid(errors)
        else:
            self.mark_valid()


# ---- Criteria / Port ----
@dataclass(frozen=True, slots=True)
class SaleCriteria:
    id: UUID | None = None
    quantity: int | None = None
    total_price: Decimal | None = None
    total_tax: Decimal | None = None
    sale_type: str | None = None  # string no .NET (FromStringForId)
    payment_type: str | None = None
    delivery_date: datetime | None = None
    sale_date: datetime | None = None
    payment_date: datetime | None = None
    id_product: UUID | None = None  # any(SaleProducts.IdProduct)
    id_customer: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
    order: str | None = None
    page: int = 1
    size: int = 10


class CustomerReader(Protocol):
    async def exists(self, customer_id: UUID) -> bool: ...


class ProductReader(Protocol):
    async def exists(self, product_id: UUID) -> bool: ...


class SaleRepository(Protocol):
    async def save(self, sale: Sale) -> None: ...

    async def find_by_id(self, sale_id: UUID) -> Sale | None: ...

    async def find_detailed_by_id(self, sale_id: UUID) -> Detailed[Sale] | None: ...

    async def search(self, criteria: SaleCriteria) -> SearchResult[Detailed[Sale]]: ...

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Detailed[Sale]]: ...

    async def disable(self, sale_id: UUID, now: datetime) -> bool: ...
