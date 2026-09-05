"""Modelos SQLAlchemy do contexto product (tabelas .NET, PascalCase).

Tipos genéricos do SQLAlchemy (`Uuid`, `DateTime`) garantem PostgreSQL=uuid/timestamp
e permitem testes de comportamento em SQLite (paridade real é validada via Testcontainers).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid


class ProductBase(DeclarativeBase):
    pass


class CategoryModel(ProductBase):
    __tablename__ = "Categories"

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    name: Mapped[str] = mapped_column("Name", String(80))
    description: Mapped[str] = mapped_column("Description", String(5000))
    short_description: Mapped[str] = mapped_column("ShortDescription", String(500))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)


class ProductModel(ProductBase):
    __tablename__ = "Products"

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    name: Mapped[str] = mapped_column("Name", Text)
    description: Mapped[str] = mapped_column("Description", String(500))
    short_description: Mapped[str] = mapped_column("ShortDescription", String(250))
    price: Mapped[Decimal] = mapped_column("Price", Numeric)
    weight: Mapped[Decimal] = mapped_column("Weight", Numeric)
    height: Mapped[Decimal] = mapped_column("Height", Numeric)
    length: Mapped[Decimal] = mapped_column("Length", Numeric)
    image: Mapped[str] = mapped_column("Image", String(5000))
    id_category: Mapped[uuid.UUID] = mapped_column(
        "IdCategory", Uuid(), ForeignKey('"Categories"."Id"')
    )
    id_company: Mapped[uuid.UUID] = mapped_column(
        "IdCompany", Uuid(), ForeignKey('"Companies"."Id"')
    )
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)

    # Includes do .NET (Category, Company, Company.CompanyAddress) sempre carregados.
    category_rel: Mapped["CategoryModel"] = relationship(
        primaryjoin="ProductModel.id_category == CategoryModel.id", lazy="joined", uselist=False
    )
    company_rel: Mapped["CompanySummaryModel"] = relationship(
        primaryjoin="ProductModel.id_company == CompanySummaryModel.id",
        lazy="joined",
        uselist=False,
    )


class CompanySummaryModel(ProductBase):
    """Projeção read-only da tabela Companies (fronteira de módulo)."""

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
