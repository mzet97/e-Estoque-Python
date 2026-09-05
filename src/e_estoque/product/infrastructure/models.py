"""Modelos SQLAlchemy do contexto product (tabelas .NET, PascalCase)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ProductBase(DeclarativeBase):
    pass


class CategoryModel(ProductBase):
    __tablename__ = "Categories"

    id: Mapped[uuid.UUID] = mapped_column("Id", PgUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column("Name", String(80))
    description: Mapped[str] = mapped_column("Description", String(5000))
    short_description: Mapped[str] = mapped_column("ShortDescription", String(500))
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)


class ProductModel(ProductBase):
    __tablename__ = "Products"

    id: Mapped[uuid.UUID] = mapped_column("Id", PgUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column("Name", Text)
    description: Mapped[str] = mapped_column("Description", String(500))
    short_description: Mapped[str] = mapped_column("ShortDescription", String(250))
    price: Mapped[Decimal] = mapped_column("Price", Numeric)
    weight: Mapped[Decimal] = mapped_column("Weight", Numeric)
    height: Mapped[Decimal] = mapped_column("Height", Numeric)
    length: Mapped[Decimal] = mapped_column("Length", Numeric)
    image: Mapped[str] = mapped_column("Image", String(5000))
    id_category: Mapped[uuid.UUID] = mapped_column(
        "IdCategory", PgUUID(as_uuid=True), ForeignKey('"Categories"."Id"')
    )
    id_company: Mapped[uuid.UUID] = mapped_column(
        "IdCompany", PgUUID(as_uuid=True), ForeignKey('"Companies"."Id"')
    )
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)


class CompanySummaryModel(ProductBase):
    """Projeção read-only da tabela Companies (fronteira de módulo)."""

    __tablename__ = "Companies"
    __mapper_args__ = {"eager_defaults": False}

    id: Mapped[uuid.UUID] = mapped_column("Id", PgUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column("Name", String(80))
    created_at: Mapped[datetime] = mapped_column(
        "CreatedAt", DateTime, server_default=func.now()
    )
