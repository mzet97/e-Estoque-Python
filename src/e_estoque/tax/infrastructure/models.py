"""Modelos SQLAlchemy do contexto tax (tabela `Taxs` — paridade do .NET)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class TaxBase(DeclarativeBase):
    pass


class TaxModel(TaxBase):
    __tablename__ = "Taxs"

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    name: Mapped[str] = mapped_column("Name", String(80))
    description: Mapped[str] = mapped_column("Description", String(250))
    percentage: Mapped[Decimal] = mapped_column("Percentage", Numeric)
    id_category: Mapped[uuid.UUID] = mapped_column(
        "IdCategory", Uuid(), ForeignKey("Categories.Id")
    )
    created_at: Mapped[datetime] = mapped_column("CreatedAt", DateTime)
    updated_at: Mapped[datetime | None] = mapped_column("UpdatedAt", DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column("DeletedAt", DateTime)
    is_deleted: Mapped[bool] = mapped_column("IsDeleted", Boolean)


class CategorySummaryModel(TaxBase):
    """Projeção read-only de Categories (include do .NET)."""

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
