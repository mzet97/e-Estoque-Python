"""Adapter `$filter` OData → SQLAlchemy via `odata-query` (executado em sqlite).

Cobre: whitelist de campos (PascalCase/camelCase), coerção tipada de literais
(uuid/datetime/bool/decimal) e erros → ValidationError (HTTP 400).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from e_estoque.filtering.odata_filter import build_odata_filter
from e_estoque.inventory.infrastructure.inventory_repository import (
    FILTER_FIELDS as INVENTORY_FIELDS,
)
from e_estoque.inventory.infrastructure.models import InventoryBase, InventoryModel
from e_estoque.product.infrastructure.category_repository import FILTER_FIELDS
from e_estoque.product.infrastructure.models import CategoryModel, ProductBase, ProductModel
from e_estoque.product.infrastructure.product_repository import (
    FILTER_FIELDS as PRODUCT_FIELDS,
)
from e_estoque.shared.domain.errors import ValidationError

_SEED_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _seed() -> Session:
    engine = create_engine("sqlite://")
    ProductBase.metadata.create_all(engine)
    session = Session(engine)
    session.add(
        CategoryModel(
            id=_SEED_ID,
            name="Bebidas",
            description="Refrigerantes e sucos",
            short_description="Geladas",
            created_at=datetime(2026, 5, 1, tzinfo=UTC),
            updated_at=None,
            deleted_at=None,
            is_deleted=False,
        )
    )
    session.commit()
    return session


def _count(filter_text: str) -> int:
    session = _seed()
    try:
        where = build_odata_filter(filter_text, CategoryModel, FILTER_FIELDS)
        stmt = select(CategoryModel)
        if where is not None:
            stmt = stmt.where(where)
        return len(session.scalars(stmt).all())
    finally:
        session.close()


def test_empty_filter_returns_none() -> None:
    assert build_odata_filter(None, CategoryModel, FILTER_FIELDS) is None
    assert build_odata_filter("  ", CategoryModel, FILTER_FIELDS) is None


def test_eq_with_pascal_case_field_matches() -> None:
    assert _count("Name eq 'Bebidas'") == 1
    assert _count("name eq 'Bebidas'") == 1
    assert _count("Name eq 'Limpeza'") == 0


def test_string_functions() -> None:
    assert _count("contains(Description,'sucos')") == 1
    assert _count("startswith(Name,'Be')") == 1
    assert _count("endswith(ShortDescription,'das')") == 1


def test_or_combination() -> None:
    assert _count("Name eq 'X' or Name eq 'Bebidas'") == 1
    assert _count("Name eq 'X' or Name eq 'Y'") == 0


def test_datetime_coercion() -> None:
    assert _count("CreatedAt gt 2020-01-01T00:00:00Z") == 1
    assert _count("CreatedAt gt 2027-01-01T00:00:00Z") == 0


def test_datetime_naive_and_date_only() -> None:
    assert _count("CreatedAt gt 2020-01-01T00:00:00") == 1  # sem Z → assume UTC
    assert _count("CreatedAt le 2027-01-01") == 1  # literal só-data


def test_uuid_coercion() -> None:
    assert _count(f"Id eq {_SEED_ID}") == 1
    assert _count(f"Id eq '{_SEED_ID}'") == 1
    assert _count("Id eq 22222222-2222-2222-2222-222222222222") == 0


def test_boolean_coercion() -> None:
    assert _count("IsDeleted eq false") == 1
    assert _count("IsDeleted eq true") == 0


def test_numeric_coercion_on_product_price() -> None:
    """Coluna numeric: literal é coerçado a Decimal antes da comparação."""
    engine = create_engine("sqlite://")
    ProductBase.metadata.create_all(engine)
    session = Session(engine)
    try:
        session.add(
            ProductModel(
                id=_SEED_ID,
                name="Coca-Cola 2L",
                description="Refrigerante garrafa 2 litros",
                short_description="Coca 2L",
                price=Decimal("9.99"),
                weight=Decimal("2.1"),
                height=Decimal("32"),
                length=Decimal("11"),
                image="https://example.com/coca.png",
                id_category=_SEED_ID,
                id_company=_SEED_ID,
                created_at=datetime(2026, 5, 1, tzinfo=UTC),
                updated_at=None,
                deleted_at=None,
                is_deleted=False,
            )
        )
        session.commit()
        where = build_odata_filter("Price gt 5.5", ProductModel, PRODUCT_FIELDS)
        assert where is not None
        assert len(session.scalars(select(ProductModel).where(where)).all()) == 1
        where_cheap = build_odata_filter("Price lt 5", ProductModel, PRODUCT_FIELDS)
        assert where_cheap is not None
        assert session.scalars(select(ProductModel).where(where_cheap)).all() == []
    finally:
        session.close()


def test_int_coercion_on_inventory_quantity() -> None:
    engine = create_engine("sqlite://")
    InventoryBase.metadata.create_all(engine)
    session = Session(engine)
    try:
        session.add(
            InventoryModel(
                id=_SEED_ID,
                quantity=10,
                date_order="2026-09-04T12:00:00",
                id_product=_SEED_ID,
                created_at=datetime(2026, 5, 1, tzinfo=UTC),
                updated_at=None,
                deleted_at=None,
                is_deleted=False,
            )
        )
        session.commit()
        where = build_odata_filter("Quantity ge 5", InventoryModel, INVENTORY_FIELDS)
        assert where is not None
        assert len(session.scalars(select(InventoryModel).where(where)).all()) == 1
    finally:
        session.close()


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        build_odata_filter("hacker eq 1", CategoryModel, FILTER_FIELDS)
    assert "Unknown filter field: hacker" in str(excinfo.value)


def test_invalid_grammar_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        build_odata_filter("name lol 'x'", CategoryModel, FILTER_FIELDS)
    assert "Invalid $filter expression" in str(excinfo.value)


def test_bad_datetime_value_rejected() -> None:
    with pytest.raises(ValidationError):
        build_odata_filter("CreatedAt gt not-a-date", CategoryModel, FILTER_FIELDS)


def test_navigation_field_rejected() -> None:
    # Whitelist não inclui navegações: Product/Category não são alcançáveis.
    with pytest.raises(ValidationError):
        build_odata_filter("Products/Name eq 'x'", CategoryModel, FILTER_FIELDS)
