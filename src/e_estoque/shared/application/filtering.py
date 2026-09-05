"""Filtros Gridify/OData: árvore de predicados + parsers (subset do contrato .NET).

Sem eval/exec — apenas parsing estruturado (proibição do §46 do master prompt).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from e_estoque.shared.domain.errors import ValidationError


class Operator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GE = "ge"
    LT = "lt"
    LE = "le"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


@dataclass(frozen=True, slots=True)
class Condition:
    field: str
    operator: Operator
    value: str


@dataclass(frozen=True, slots=True)
class And:
    children: list[FilterNode] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Or:
    children: list[FilterNode] = field(default_factory=list)


FilterNode = And | Or | Condition


@dataclass(frozen=True, slots=True)
class OrderTerm:
    field: str
    descending: bool


def _split_outside_quotes(text: str, pattern: str) -> list[str]:
    """Split por separador ignorando o conteúdo dentro de aspas simples."""
    parts: list[str] = []
    buf: list[str] = []
    quoted = False
    i = 0
    while i < len(text):
        chunk = text[i : i + len(pattern)]
        if not quoted and pattern and chunk == pattern:
            parts.append("".join(buf))
            buf = []
            i += len(pattern)
            continue
        ch = text[i]
        if ch == "'":
            quoted = not quoted
        buf.append(ch)
        i += 1
    parts.append("".join(buf))
    return parts


def _unquote(value: str) -> str:
    if len(value) >= 2 and value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def parse_gridify_filter(filter_text: str | None) -> FilterNode | None:
    """Subset Gridify: & (AND), | (OR), =, ==, !=, >, <, >=, <=, ^=, $=, *= e =*v*."""
    if not filter_text or not filter_text.strip():
        return None
    or_groups: list[FilterNode] = []
    for or_part in _split_outside_quotes(filter_text, "|"):
        ands: list[FilterNode] = []
        for and_part in _split_outside_quotes(or_part, "&"):
            ands.append(_parse_gridify_condition(and_part.strip()))
        or_groups.append(ands[0] if len(ands) == 1 else And(children=ands))
    return or_groups[0] if len(or_groups) == 1 else Or(children=or_groups)


def _parse_gridify_condition(condition: str) -> Condition:
    for op in ("==", "!=", ">=", "<=", "^=", "$=", "*=", "=", ">", "<"):
        idx = condition.find(op)
        if idx <= 0:
            continue
        field_name = condition[:idx].strip()
        raw = condition[idx + len(op) :].strip()
        operator: Operator = {
            "==": Operator.EQ,
            "=": Operator.EQ,
            "!=": Operator.NE,
            ">=": Operator.GE,
            "<=": Operator.LE,
            "^=": Operator.STARTS_WITH,
            "$=": Operator.ENDS_WITH,
            "*=": Operator.CONTAINS,
            ">": Operator.GT,
            "<": Operator.LT,
        }[op]
        if operator is Operator.EQ and raw.startswith("*"):
            operator = Operator.CONTAINS
            raw = raw[1:-1] if raw.endswith("*") else raw[1:]
        elif operator is Operator.CONTAINS and raw.startswith("*") and raw.endswith("*"):
            raw = raw[1:-1]
        if not field_name:
            raise ValidationError(f"Invalid gridify filter: {condition}")
        return Condition(field_name, operator, _unquote(raw))
    raise ValidationError(f"Invalid gridify filter: {condition}")


def parse_order_by(order_by: str | None) -> list[OrderTerm]:
    """'name asc, createdAt desc' → termos; suporta sintaxe Gridify e OData."""
    if not order_by or not order_by.strip():
        return []
    terms: list[OrderTerm] = []
    for part in order_by.split(","):
        token = part.strip()
        if not token:
            continue
        pieces = token.split()
        descending = len(pieces) > 1 and pieces[1].lower() in ("desc", "descending")
        terms.append(OrderTerm(pieces[0], descending))
    return terms
