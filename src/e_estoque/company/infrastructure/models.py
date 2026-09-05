"""Modelos SQLAlchemy do contexto company (tabela Companies, colunas owned address)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class CompanyBase(DeclarativeBase):
    pass


class CompanyModel(CompanyBase):
    __tablename__ = "Companies"

    id: Mapped[uuid.UUID] = mapped_column("Id", Uuid(), primary_key=True)
    name: Mapped[str] = mapped_column("Name", String(80))
    doc_id: Mapped[str] = mapped_column("DocId", String(80))
    email: Mapped[str] = mapped_column("Email", String(250))
    description: Mapped[str] = mapped_column("Description", String(250))
    phone_number: Mapped[str] = mapped_column("PhoneNumber", String(80))
    # Value object owned do .NET: colunas inline com o prefixo CompanyAddress_
    # (`_County` é a grafia da coluna do campo `country` — paridade do schema).
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
