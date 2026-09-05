"""$filter OData → SQLAlchemy via a biblioteca `odata-query` (ADR-013).

A biblioteca fornece a gramática robusta (lexer/parser sly, AST tipada) e a
tradução ORM; este adapter acrescenta as garantias do contrato:

1. **Whitelist de campos** — `visit_Identifier` resolve nomes OData
   (PascalCase/camelCase) apenas no FieldMap da entidade; campo fora da
   whitelist → ValidationError (HTTP 400). Navegações/relacionamentos ficam
   bloqueados (só colunas mapeadas).
2. **Coerção tipada de literais** — uuid/datetime/decimal/int convertidos para
   o `python_type` da coluna comparada (drivers como asyncpg são estritos).
3. **Erros → 400** — falhas de gramática/valor viram `ValidationError` com
   mensagens no padrão do contrato.
"""

from __future__ import annotations

import uuid as uuid_module
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from odata_query import ast as odata_ast
from odata_query.exceptions import ParsingException, TokenizingException
from odata_query.grammar import ODataLexer, ODataParser
from odata_query.sqlalchemy.orm import AstToSqlAlchemyOrmVisitor
from sqlalchemy import literal
from sqlalchemy.sql.elements import BindParameter, ColumnElement

from e_estoque.shared.domain.errors import ValidationError
from e_estoque.shared.infrastructure.sql_filtering import FieldMap

_LITERAL_NODES = (
    odata_ast.Integer,
    odata_ast.Float,
    odata_ast.String,
    odata_ast.GUID,
    odata_ast.Date,
    odata_ast.DateTime,
    odata_ast.Time,
)


class WhitelistOrmVisitor(AstToSqlAlchemyOrmVisitor):
    """Visitor da lib com resolução de campos por whitelist e coerção tipada."""

    def __init__(self, root_model: Any, fields: FieldMap) -> None:
        super().__init__(root_model)
        self._fields = fields

    def visit_Identifier(self, node: odata_ast.Identifier) -> Any:
        field_def = self._fields.get(node.name.lower())
        if field_def is None:
            raise ValidationError(f"Unknown filter field: {node.name}")
        attribute: Any = self.root_model
        for part in field_def.column.split("."):
            attribute = getattr(attribute, part)
        return attribute

    def visit_Compare(self, node: odata_ast.Compare) -> Any:
        left = self.visit(node.left)
        right = self.visit(node.right)
        comparator = self.visit(node.comparator)
        if isinstance(node.right, _LITERAL_NODES):
            right = _coerce_literal(left, right, node.right)
        result: Any = comparator(left, right)
        return result


def _coerce_literal(left: Any, right: Any, literal_node: Any) -> Any:
    """Coage o literal ao python_type da coluna (asyncpg/PG são estritos)."""
    python_type = getattr(getattr(left, "type", None), "python_type", None)
    raw_value = getattr(right, "value", None)
    if python_type is None or not isinstance(right, BindParameter):
        return right
    try:
        if python_type is uuid_module.UUID:
            return literal(uuid_module.UUID(str(raw_value)))
        if python_type is Decimal:
            return literal(Decimal(str(raw_value)))
        if python_type is datetime:
            return literal(_parse_datetime(str(raw_value)))
        if python_type is date:
            return literal(date.fromisoformat(str(raw_value)[:10]))
        if python_type is int:
            return literal(int(str(raw_value)))
        if python_type is float:
            return literal(float(str(raw_value)))
    except (ValueError, TypeError, InvalidOperation) as exc:
        raise ValidationError(f"Invalid filter value '{raw_value}'") from exc
    return right


def _parse_datetime(raw: str) -> datetime:
    normalized = raw.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def build_odata_filter(
    filter_text: str | None, model: Any, fields: FieldMap
) -> ColumnElement[bool] | None:
    """Converte `$filter` OData → predicado SQLAlchemy (None se vazio)."""
    if not filter_text or not filter_text.strip():
        return None
    try:
        tree = ODataParser().parse(ODataLexer().tokenize(filter_text))
        predicate: ColumnElement[bool] | None = (
            None if tree is None else WhitelistOrmVisitor(model, fields).visit(tree)
        )
    except ValidationError:
        raise
    except (TokenizingException, ParsingException) as exc:
        raise ValidationError(f"Invalid $filter expression: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - qualquer falha de gramática vira 400
        raise ValidationError("Invalid $filter expression") from exc
    return predicate
