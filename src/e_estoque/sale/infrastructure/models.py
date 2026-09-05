"""Modelos SQLAlchemy do contexto sales (Sales, SaleProducts + projeções)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid


class SaleBase(DeclarativeBase):
    pass


class SaleModel(SaleBase):
    __tablename__ = "Sales"

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    quantity: Mapped[int] = mapped_column("Quantity", Integer)
    total_price: Mapped[Decimal] = mapped_column("TotalPrice", Numeric)
    total_tax: Mapped[Decimal] = mapped_column("TotalTax", Numeric)
    sale_type: Mapped[int] = mapped_column("SaleType", Integer)
    payment_type: Mapped[int] = mapped_column("PaymentType", Integer)
    delivery_date: Mapped[datetime] = mapped_column("DeliveryDate", DateTime)
    sale_date: Mapped[datetime] = mapped_column("SaleDate", DateTime)
    payment_date: Mapped[datetime] = mapped_column("PaymentDate", DateTime)
    id_customer: Mapped[uuid.UUID] = mapped_column(
        "IdCustomer", Uuid(), ForeignKey('"Customers"."Id"')
    )
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)

    # Includes do .NET: Customer, SaleProduct, SaleProduct.Product
    customer_rel: Mapped["CustomerSummaryModel"] = relationship(
        primaryjoin="SaleModel.id_customer == CustomerSummaryModel.id",
        lazy="selectin",
        uselist=False,
    )
    sale_products: Mapped[list["SaleProductModel"]] = relationship(
        primaryjoin="SaleModel.id == SaleProductModel.id_sale",
        lazy="selectin",
        cascade="save-update, merge, delete",
    )


class SaleProductModel(SaleBase):
    __tablename__ = "SaleProducts"

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    quantity: Mapped[int] = mapped_column("Quantity", Integer)
    id_product: Mapped[uuid.UUID] = mapped_column(
        "IdProduct", Uuid(), ForeignKey('"Products"."Id"')
    )
    id_sale: Mapped[uuid.UUID] = mapped_column("IdSale", Uuid(), ForeignKey('"Sales"."Id"'))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)

    product_rel: Mapped["ProductSummaryModel"] = relationship(
        primaryjoin="SaleProductModel.id_product == ProductSummaryModel.id",
        lazy="selectin",
        uselist=False,
    )


class CustomerSummaryModel(SaleBase):
    """Projeção read-only de Customers (endereço inline)."""

    __tablename__ = "Customers"
    __mapper_args__ = {"eager_defaults": False}

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    name: Mapped[str] = mapped_column("Name", String(80))
    doc_id: Mapped[str] = mapped_column("DocId", String(80))
    email: Mapped[str] = mapped_column("Email", String(80))
    description: Mapped[str] = mapped_column("Description", String(250))
    phone_number: Mapped[str] = mapped_column("PhoneNumber", String(80))
    address_street: Mapped[str] = mapped_column("CustomerAddress_Street", String(80))
    address_number: Mapped[str] = mapped_column("CustomerAddress_Number", String(80))
    address_complement: Mapped[str] = mapped_column("CustomerAddress_Complement", String(80))
    address_neighborhood: Mapped[str] = mapped_column("CustomerAddress_Neighborhood", String(80))
    address_district: Mapped[str] = mapped_column("CustomerAddress_District", String(80))
    address_city: Mapped[str] = mapped_column("CustomerAddress_City", String(80))
    address_country: Mapped[str] = mapped_column("CustomerAddress_County", String(80))
    address_zip_code: Mapped[str] = mapped_column("CustomerAddress_ZipCode", String(80))
    address_latitude: Mapped[str] = mapped_column("CustomerAddress_Latitude", String(80))
    address_longitude: Mapped[str] = mapped_column("CustomerAddress_Longitude", String(80))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)


class ProductSummaryModel(SaleBase):
    """Projeção read-only de Products (+ Category/Company) para os includes."""

    __tablename__ = "Products"
    __mapper_args__ = {"eager_defaults": False}

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    name: Mapped[str] = mapped_column("Name", String(250))
    description: Mapped[str] = mapped_column("Description", String(500))
    short_description: Mapped[str] = mapped_column("ShortDescription", String(250))
    image: Mapped[str] = mapped_column("Image", String(5000))
    price: Mapped[Decimal] = mapped_column("Price", Numeric)
    weight: Mapped[Decimal] = mapped_column("Weight", Numeric)
    height: Mapped[Decimal] = mapped_column("Height", Numeric)
    length: Mapped[Decimal] = mapped_column("Length", Numeric)
    id_category: Mapped[uuid.UUID] = mapped_column("IdCategory", Uuid())
    id_company: Mapped[uuid.UUID] = mapped_column("IdCompany", Uuid())
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)

    category_rel: Mapped["CategorySummaryModel | None"] = relationship(
        primaryjoin="ProductSummaryModel.id_category == CategorySummaryModel.id",
        lazy="selectin",
        uselist=False,
    )
    company_rel: Mapped["CompanySummaryModel | None"] = relationship(
        primaryjoin="ProductSummaryModel.id_company == CompanySummaryModel.id",
        lazy="selectin",
        uselist=False,
    )


class CategorySummaryModel(SaleBase):
    """Projeção read-only de Categories."""

    __tablename__ = "Categories"
    __mapper_args__ = {"eager_defaults": False}

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    name: Mapped[str] = mapped_column("Name", String(80))
    description: Mapped[str] = mapped_column("Description", String(5000))
    short_description: Mapped[str] = mapped_column("ShortDescription", String(500))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)


class CompanySummaryModel(SaleBase):
    """Projeção read-only de Companies (endereço inline)."""

    __tablename__ = "Companies"
    __mapper_args__ = {"eager_defaults": False}

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    name: Mapped[str] = mapped_column("Name", String(80))
    doc_id: Mapped[str] = mapped_column("DocId", String(80))
    email: Mapped[str] = mapped_column("Email", String(250))
    description: Mapped[str] = mapped_column("Description", String(250))
    phone_number: Mapped[str] = mapped_column("PhoneNumber", String(80))
    address_street: Mapped[str] = mapped_column("CompanyAddress_Street", String(80))
    address_number: Mapped[str] = mapped_column("CompanyAddress_Number", String(80))
    address_complement: Mapped[str] = mapped_column("CompanyAddress_Complement", String(80))
    address_neighborhood: Mapped[str] = mapped_column("CompanyAddress_Neighborhood", String(80))
    address_district: Mapped[str] = mapped_column("CompanyAddress_District", String(80))
    address_city: Mapped[str] = mapped_column("CompanyAddress_City", String(80))
    address_country: Mapped[str] = mapped_column("CompanyAddress_County", String(80))
    address_zip_code: Mapped[str] = mapped_column("CompanyAddress_ZipCode", String(80))
    address_latitude: Mapped[str] = mapped_column("CompanyAddress_Latitude", String(80))
    address_longitude: Mapped[str] = mapped_column("CompanyAddress_Longitude", String(80))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)
