"""Modelos SQLAlchemy do contexto inventory + projeções de Product/Category/Company.

Paridade: a tabela é `inventories` (minúsculas) e `DateOrder` é `varchar(80)` —
o domínio valida datetime e o repositório serializa ISO-8601 (ASSUMPTIONS A-01).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class InventoryBase(DeclarativeBase):
    pass


class InventoryModel(InventoryBase):
    __tablename__ = "inventories"

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    quantity: Mapped[int] = mapped_column("Quantity", Integer)
    date_order: Mapped[str] = mapped_column("DateOrder", String(80))
    id_product: Mapped[uuid.UUID] = mapped_column("IdProduct", Uuid(), ForeignKey("Products.Id"))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)


class ProductSummaryModel(InventoryBase):
    """Projeção read-only de Products (+ Category/Company) para os includes .NET."""

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


class CategorySummaryModel(InventoryBase):
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


class CompanySummaryModel(InventoryBase):
    """Projeção read-only de Companies (colunas de endereço incluídas)."""

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
