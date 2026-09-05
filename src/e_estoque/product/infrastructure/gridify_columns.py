"""Whitelist de colunas gridify por contexto (expressões estáticas)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import and_, or_

from e_estoque.product.infrastructure.models import CategoryModel, ProductModel
from e_estoque.shared.application.filtering import (
    FilterNode,
    Operator,
)
from e_estoque.shared.domain.errors import ValidationError

CATEGORY_COLUMNS = {
    "id": CategoryModel.id,
    "name": CategoryModel.name,
    "description": CategoryModel.description,
    "shortdescription": CategoryModel.short_description,
    "createdat": CategoryModel.created_at,
    "updatedat": CategoryModel.updated_at,
    "deletedat": CategoryModel.deleted_at,
    "isdeleted": CategoryModel.is_deleted,
}
CATEGORY_ORDER = {
    "name": CategoryModel.name,
    "description": CategoryModel.description,
    "shortdescription": CategoryModel.short_description,
    "createdat": CategoryModel.created_at,
    "updatedat": CategoryModel.updated_at,
    "deletedat": CategoryModel.deleted_at,
}
PRODUCT_COLUMNS = {
    "id": ProductModel.id,
    "name": ProductModel.name,
    "description": ProductModel.description,
    "shortdescription": ProductModel.short_description,
    "price": ProductModel.price,
    "weight": ProductModel.weight,
    "height": ProductModel.height,
    "length": ProductModel.length,
    "image": ProductModel.image,
    "idcategory": ProductModel.id_category,
    "idcompany": ProductModel.id_company,
    "createdat": ProductModel.created_at,
    "updatedat": ProductModel.updated_at,
    "deletedat": ProductModel.deleted_at,
    "isdeleted": ProductModel.is_deleted,
}
PRODUCT_ORDER = {
    "name": ProductModel.name,
    "description": ProductModel.description,
    "shortdescription": ProductModel.short_description,
    "price": ProductModel.price,
    "weight": ProductModel.weight,
    "height": ProductModel.height,
    "length": ProductModel.length,
    "createdat": ProductModel.created_at,
    "updatedat": ProductModel.updated_at,
    "deletedat": ProductModel.deleted_at,
}


def _typed(col: Any, raw: str) -> Any:
    py_type = col.type.python_type
    if py_type is Decimal:
        return Decimal(raw)
    if py_type is bool:
        return raw.lower() == "true"
    try:
        return py_type(raw)
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"Invalid filter value '{raw}'") from exc


def _apply(col: Any, op: Operator, raw: str) -> Any:
    if op is Operator.CONTAINS and col.type.python_type is str:
        return col.contains(raw, autoescape=True)
    if op is Operator.STARTS_WITH and col.type.python_type is str:
        return col.startswith(raw, autoescape=True)
    if op is Operator.ENDS_WITH and col.type.python_type is str:
        return col.endswith(raw, autoescape=True)
    value = _typed(col, raw)
    if op is Operator.EQ:
        return col == value
    if op is Operator.NE:
        return col != value
    if op is Operator.GT:
        return col > value
    if op is Operator.GE:
        return col >= value
    if op is Operator.LT:
        return col < value
    if op is Operator.LE:
        return col <= value
    raise ValidationError(f"Operador não suportado: {op}")


def _build_where(node: FilterNode | None, columns: dict[str, Any]) -> Any:
    if node is None:
        return None
    from e_estoque.shared.application.filtering import And, Or

    if isinstance(node, And):
        parts = [_build_where(child, columns) for child in node.children]
        return and_(*parts)
    if isinstance(node, Or):
        parts = [_build_where(child, columns) for child in node.children]
        return or_(*parts)
    col = columns.get(node.field.lower())
    if col is None:
        raise ValidationError(f"Unknown filter field: {node.field}")
    return _apply(col, node.operator, node.value)


def _build_order(order_text: str | None, order_map: dict[str, Any]) -> list[Any]:
    from sqlalchemy import asc, desc

    from e_estoque.shared.application.filtering import parse_order_by

    terms = parse_order_by(order_text)
    if not terms:
        return []
    cols: list[Any] = []
    for term in terms:
        col = order_map.get(term.field.lower())
        if col is None:
            raise ValidationError(f"Unknown order field: {term.field}")
        cols.append(desc(col) if term.descending else asc(col))
    return cols


def category_where(node: FilterNode | None) -> Any:
    return _build_where(node, CATEGORY_COLUMNS)


def category_order(order_text: str | None) -> list[Any]:
    return _build_order(order_text, CATEGORY_ORDER)


def product_where(node: FilterNode | None) -> Any:
    return _build_where(node, PRODUCT_COLUMNS)


def product_order(order_text: str | None) -> list[Any]:
    return _build_order(order_text, PRODUCT_ORDER)
