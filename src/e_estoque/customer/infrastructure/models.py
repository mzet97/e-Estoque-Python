"""Modelos SQLAlchemy do contexto customer (tabela Customers, Email varchar(80))."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid


class CustomerBase(DeclarativeBase):
    pass


class CustomerModel(CustomerBase):
    __tablename__ = "Customers"

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
