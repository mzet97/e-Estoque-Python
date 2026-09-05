"""View models da API (contrato camelCase do .NET; publicados no shared).

Espelham os *ViewModel .NET: BaseViewModel = {id, createdAt, updatedAt, deletedAt}
( sem isDeleted ) + campos por entidade. Decimais serializam como número JSON.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PlainSerializer
from pydantic.alias_generators import to_camel

from e_estoque.shared.application.read_models import (
    CategorySummary,
    CompanySummary,
    CustomerSummary,
    Detailed,
    ProductSummary,
)


def _decimal_number(value: Decimal) -> int | float:
    """Decimal → número JSON (paridade com o System.Text.Json .NET)."""
    if value == value.to_integral_value():
        return int(value)
    return float(value)


DecimalNumber = Annotated[Decimal, PlainSerializer(_decimal_number, return_type=float)]


class _View(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class AddressView(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

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


class CategoryView(_View):
    name: str
    description: str
    short_description: str


class CompanyView(_View):
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    company_address: AddressView


class CustomerView(_View):
    name: str
    doc_id: str
    email: str
    description: str
    phone_number: str
    customer_address: AddressView


class ProductView(_View):
    name: str
    description: str
    short_description: str
    image: str
    price: DecimalNumber
    weight: DecimalNumber
    height: DecimalNumber
    length: DecimalNumber
    id_category: UUID
    category: CategoryView | None = None
    id_company: UUID
    company: CompanyView | None = None


class InventoryView(_View):
    quantity: int
    date_order: str
    id_product: UUID
    product: ProductView | None = None


class SaleView(_View):
    quantity: int
    total_price: DecimalNumber
    total_tax: DecimalNumber
    sale_type: int
    payment_type: int
    delivery_date: datetime
    sale_date: datetime
    payment_date: datetime
    id_customer: UUID
    customer: CustomerView | None = None
    products: list[ProductView] = []


class TaxView(_View):
    name: str
    description: str
    percentage: DecimalNumber
    id_category: UUID
    category: CategoryView | None = None


# ---- mapeadores Detailed/Summary → View (equivalente aos FromEntity .NET) ----
class _Audited(Protocol):
    @property
    def id(self) -> UUID: ...

    @property
    def created_at(self) -> datetime: ...

    @property
    def updated_at(self) -> datetime | None: ...

    @property
    def deleted_at(self) -> datetime | None: ...


class ProductLike(_Audited, Protocol):
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


class InventoryLike(_Audited, Protocol):
    quantity: int
    date_order: datetime
    id_product: UUID


class TaxLike(_Audited, Protocol):
    name: str
    description: str
    percentage: Decimal
    id_category: UUID


class SaleLike(_Audited, Protocol):
    """SaleLike com propriedades (IntEnum <: int pela covariância de leitura)."""

    @property
    def quantity(self) -> int: ...

    @property
    def total_price(self) -> Decimal: ...

    @property
    def total_tax(self) -> Decimal: ...

    @property
    def sale_type(self) -> int: ...

    @property
    def payment_type(self) -> int: ...

    @property
    def delivery_date(self) -> datetime | None: ...

    @property
    def sale_date(self) -> datetime: ...

    @property
    def payment_date(self) -> datetime | None: ...

    @property
    def id_customer(self) -> UUID: ...


def _address(value: Any) -> AddressView:
    return AddressView(**dataclasses.asdict(value))


def category_view(summary: CategorySummary) -> CategoryView:
    return CategoryView(
        id=summary.id,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        deleted_at=summary.deleted_at,
        name=summary.name,
        description=summary.description,
        short_description=summary.short_description,
    )


def company_view(summary: CompanySummary) -> CompanyView:
    return CompanyView(
        id=summary.id,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        deleted_at=summary.deleted_at,
        name=summary.name,
        doc_id=summary.doc_id,
        email=summary.email,
        description=summary.description,
        phone_number=summary.phone_number,
        company_address=_address(summary.company_address),
    )


def customer_view(summary: CustomerSummary) -> CustomerView:
    return CustomerView(
        id=summary.id,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        deleted_at=summary.deleted_at,
        name=summary.name,
        doc_id=summary.doc_id,
        email=summary.email,
        description=summary.description,
        phone_number=summary.phone_number,
        customer_address=_address(summary.customer_address),
    )


def product_summary_view(summary: ProductSummary) -> ProductView:
    return ProductView(
        id=summary.id,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        deleted_at=summary.deleted_at,
        name=summary.name,
        description=summary.description,
        short_description=summary.short_description,
        image=summary.image,
        price=summary.price,
        weight=summary.weight,
        height=summary.height,
        length=summary.length,
        id_category=summary.id_category,
        category=category_view(summary.category) if summary.category else None,
        id_company=summary.id_company,
        company=company_view(summary.company) if summary.company else None,
    )


def product_view[T: ProductLike](detailed: Detailed[T]) -> ProductView:
    """View de Product a partir da entidade + summaries (includes .NET)."""
    entity = detailed.entity
    return ProductView(
        id=entity.id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        deleted_at=entity.deleted_at,
        name=entity.name,
        description=entity.description,
        short_description=entity.short_description,
        image=entity.image,
        price=entity.price,
        weight=entity.weight,
        height=entity.height,
        length=entity.length,
        id_category=entity.id_category,
        category=category_view(detailed.category) if detailed.category else None,
        id_company=entity.id_company,
        company=company_view(detailed.company) if detailed.company else None,
    )


def inventory_view[T: InventoryLike](detailed: Detailed[T]) -> InventoryView:
    entity = detailed.entity
    return InventoryView(
        id=entity.id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        deleted_at=entity.deleted_at,
        quantity=entity.quantity,
        date_order=entity.date_order.isoformat(),
        id_product=entity.id_product,
        product=product_summary_view(detailed.product) if detailed.product else None,
    )


def tax_view[T: TaxLike](detailed: Detailed[T]) -> TaxView:
    entity = detailed.entity
    return TaxView(
        id=entity.id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        deleted_at=entity.deleted_at,
        name=entity.name,
        description=entity.description,
        percentage=entity.percentage,
        id_category=entity.id_category,
        category=category_view(detailed.category) if detailed.category else None,
    )


def sale_view[T: SaleLike](detailed: Detailed[T]) -> SaleView:
    entity = detailed.entity
    # SaleValidation garante datas não nulas nas vendas expostas pelo contrato.
    assert entity.delivery_date is not None
    assert entity.payment_date is not None
    return SaleView(
        id=entity.id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        deleted_at=entity.deleted_at,
        quantity=entity.quantity,
        total_price=entity.total_price,
        total_tax=entity.total_tax,
        sale_type=int(entity.sale_type),
        payment_type=int(entity.payment_type),
        delivery_date=entity.delivery_date,
        sale_date=entity.sale_date,
        payment_date=entity.payment_date,
        id_customer=entity.id_customer,
        customer=customer_view(detailed.customer) if detailed.customer else None,
        products=[product_summary_view(p) for p in detailed.products],
    )
