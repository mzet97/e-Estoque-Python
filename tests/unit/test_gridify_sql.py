"""Gridify → SQLAlchemy (`build_filter`): operadores de string, and/or e erros."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from e_estoque.product.infrastructure.category_repository import FILTER_FIELDS
from e_estoque.product.infrastructure.models import CategoryModel, ProductBase
from e_estoque.shared.application.filtering import And, Condition, Operator, parse_gridify_filter
from e_estoque.shared.domain.errors import ValidationError
from e_estoque.shared.infrastructure.sql_filtering import build_filter

_SEED_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _session() -> Session:
    engine = create_engine("sqlite://")
    ProductBase.metadata.create_all(engine)
    session = Session(engine)
    session.add(
        CategoryModel(
            id=_SEED_ID,
            name="Bebidas geladas",
            description="Refrigerantes e sucos gelados",
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
    session = _session()
    try:
        where = build_filter(parse_gridify_filter(filter_text), CategoryModel, FILTER_FIELDS)
        stmt = select(CategoryModel)
        if where is not None:
            stmt = stmt.where(where)
        return len(session.scalars(stmt).all())
    finally:
        session.close()


def test_contains_operator() -> None:
    assert _count("description*=sucos") == 1
    assert _count("description=*existe*") == 0


def test_starts_with_and_ends_with() -> None:
    assert _count("name^=Bebidas") == 1
    assert _count("name$=geladas") == 1
    assert _count("name^=Outra") == 0


def test_and_or_combinations() -> None:
    assert _count("name^=Bebidas&isDeleted=false") == 1
    assert _count("name^=Bebidas|name^=Outra") == 1


def test_numeric_and_uuid_fields() -> None:
    assert _count(f"id={_SEED_ID}") == 1
    assert _count("isdeleted=false") == 1


def test_unknown_field_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        _count("hacker=1")
    assert "Unknown filter field: hacker" in str(excinfo.value)


def test_direct_condition_build() -> None:
    where = build_filter(
        Condition("name", Operator.EQ, "Bebidas geladas"), CategoryModel, FILTER_FIELDS
    )
    session = _session()
    try:
        assert where is not None
        assert len(session.scalars(select(CategoryModel).where(where)).all()) == 1
    finally:
        session.close()


def test_and_node_with_multiple_children() -> None:
    node = And(
        children=[
            Condition("name", Operator.EQ, "Bebidas geladas"),
            Condition("isDeleted", Operator.EQ, "false"),
        ]
    )
    where = build_filter(node, CategoryModel, FILTER_FIELDS)
    session = _session()
    try:
        assert where is not None
        assert len(session.scalars(select(CategoryModel).where(where)).all()) == 1
    finally:
        session.close()
