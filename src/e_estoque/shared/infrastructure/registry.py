"""Registry dos metadados SQLAlchemy (bases por contexto) para testes e Alembic."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import DeclarativeBase

from e_estoque.company.infrastructure.models import CompanyBase
from e_estoque.customer.infrastructure.models import CustomerBase
from e_estoque.inventory.infrastructure.models import InventoryBase
from e_estoque.product.infrastructure.models import ProductBase
from e_estoque.sale.infrastructure.models import SaleBase
from e_estoque.tax.infrastructure.models import TaxBase

ALL_BASES: list[type[DeclarativeBase]] = [
    ProductBase,
    CompanyBase,
    CustomerBase,
    InventoryBase,
    SaleBase,
    TaxBase,
]


def create_all(bind: Any) -> None:
    """Criação para TESTES (produção usa Alembic — nunca create_all)."""
    for base in ALL_BASES:
        base.metadata.create_all(bind=bind)


def drop_all(bind: Any) -> None:
    for base in reversed(ALL_BASES):
        base.metadata.drop_all(bind=bind)
