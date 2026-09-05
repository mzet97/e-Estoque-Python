"""Tradução de FilterNode (gridify/odata) → SQLAlchemy expressions, com whitelist."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any

from sqlalchemy import Column, and_, or_
from sqlalchemy.sql.elements import ColumnElement

from e_estoque.shared.application.filtering import (
    And,
    Condition,
    FilterNode,
    Operator,
    parse_order_by,
)
from e_estoque.shared.domain.errors import ValidationError


class FieldType(StrEnum):
    STRING = "string"
    NUMBER = "number"
    INSTANT = "instant"
    BOOLEAN = "boolean"
    UUID = "uuid"


@dataclass(frozen=True, slots=True)
class FieldDef:
    column: str  # nome do atributo no model SQLAlchemy
    type: FieldType


FieldMap = dict[str, FieldDef]


def _resolve(model: Any, dotted: str) -> ColumnElement[Any] | Column[Any]:
    part: Any = model
    for name in dotted.split("."):
        part = getattr(part, name)
    result: ColumnElement[Any] | Column[Any] = part
    return result


def _convert(field_type: FieldType, raw: str) -> Any:
    try:
        match field_type:
            case FieldType.NUMBER:
                return Decimal(raw)
            case FieldType.INSTANT:
                return datetime.fromisoformat(raw)
            case FieldType.BOOLEAN:
                return raw.lower() == "true"
            case FieldType.UUID:
                return uuid.UUID(raw)
            case _:
                return raw
    except (ValueError, InvalidOperation) as exc:
        raise ValidationError(f"Invalid filter value '{raw}'") from exc


def _condition(condition: Condition, model: Any, fields: FieldMap, cb: Any) -> ColumnElement[bool]:
    fdef = fields.get(condition.field.lower())
    if fdef is None:
        raise ValidationError(f"Unknown filter field: {condition.field}")
    col = _resolve(model, fdef.column)
    value = _convert(fdef.type, condition.value)
    op = condition.operator
    if fdef.type is FieldType.STRING:
        low = col.lower() if hasattr(col, "lower") else col
        match op:
            case Operator.EQ:
                return _clause(col == condition.value)
            case Operator.NE:
                return _clause(col != condition.value)
            case Operator.CONTAINS:
                return _clause(low.like(f"%{_escape_like(condition.value.lower())}%", escape="\\"))
            case Operator.STARTS_WITH:
                return _clause(low.like(f"{_escape_like(condition.value.lower())}%", escape="\\"))
            case Operator.ENDS_WITH:
                return _clause(low.like(f"%{_escape_like(condition.value.lower())}", escape="\\"))
            case _:
                raise ValidationError(f"Operator {op} not supported for strings")
    match op:
        case Operator.EQ:
            return _clause(col == value)
        case Operator.NE:
            return _clause(col != value)
        case Operator.GT:
            return _clause(col > value)
        case Operator.GE:
            return _clause(col >= value)
        case Operator.LT:
            return _clause(col < value)
        case Operator.LE:
            return _clause(col <= value)
        case _:
            raise ValidationError(f"Operator {op} not supported for {fdef.type}")


def _clause(element: Any) -> ColumnElement[bool]:
    """Narrowing explícita do elemento SQLAlchemy gerado (sempre parametrizado)."""
    result: ColumnElement[bool] = element
    return result


def _escape_like(value: str) -> str:
    """Escapa wildcards de LIKE para que o valor seja literal (defesa extra)."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def build_filter(
    node: FilterNode | None, model: Any, fields: FieldMap
) -> ColumnElement[bool] | None:
    """Converte FilterNode → SQLAlchemy predicate (AND/OR/condição)."""
    if node is None:
        return None
    if isinstance(node, Condition):
        return _condition(node, model, fields, None)
    children: list[ColumnElement[bool]] = []
    for child in node.children:
        predicate = build_filter(child, model, fields)
        if predicate is not None:
            children.append(predicate)
    if not children:
        return None
    if isinstance(node, And):
        return and_(*children)
    return or_(*children)


def order_columns(order_by: str | None, model: Any, fields: FieldMap) -> list[Any]:
    """Termos de ordenação com whitelist; default id ASC."""
    from sqlalchemy import asc, desc

    terms = parse_order_by(order_by)
    if not terms:
        return [asc(_resolve(model, "id"))]
    columns: list[Any] = []
    for term in terms:
        fdef = fields.get(term.field.lower())
        if fdef is None:
            raise ValidationError(f"Unknown order field: {term.field}")
        col = _resolve(model, fdef.column)
        columns.append(desc(col) if term.descending else asc(col))
    return columns
