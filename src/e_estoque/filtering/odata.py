"""OData v4 (subset) — adapter seguro para SQLAlchemy (ADR-013).

Suporta: $filter (eq/ne/gt/ge/lt/le, contains/startswith/endswith, and/or),
$orderby, $top (≤1000)/$skip, $count=true, /$count, ({key}), $select.
Resposta no shape do ASP.NET OData ({@odata.context, value}); propriedades
PascalCase (contrato C#). Parsing estruturado com whitelist — sem eval/exec.
Execução de statements somente pelos helpers de `shared.infrastructure.paging`
(consulta totalmente parametrizada, valores sempre vinculados pelo SQLAlchemy).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from e_estoque.filtering.odata_filter import build_odata_filter
from e_estoque.shared.application.filtering import Condition, Operator
from e_estoque.shared.domain.errors import NotFoundError, ValidationError
from e_estoque.shared.infrastructure.db import open_session
from e_estoque.shared.infrastructure.paging import count_rows, first_row, page_rows
from e_estoque.shared.infrastructure.sql_filtering import (
    FieldDef,
    FieldType,
    build_filter,
    order_columns,
)

MAX_TOP = 1000

_KEY_PATH = re.compile(r"([A-Za-z]+)\((.+)\)")


@dataclass(frozen=True, slots=True)
class EntitySetSpec:
    """Registro de um entity set OData (model + whitelist de campos)."""

    name: str
    model: Any
    fields: dict[str, FieldDef]
    columns: tuple[str, ...]


def _pascal(key: str) -> str:
    return "".join(part.capitalize() or "_" for part in key.split("_"))


def _model_to_dict(model: Any, columns: tuple[str, ...] | list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for column in columns:
        value = getattr(model, column)
        out[_pascal(column)] = value.isoformat() if hasattr(value, "isoformat") else value
    return out


def build_router(sets: list[EntitySetSpec]) -> APIRouter:
    """Constrói /odata/{Set}, /odata/{Set}(key), /odata/{Set}/$count e /$metadata."""
    router = APIRouter(prefix="/odata", tags=["OData"])
    by_name = {spec.name: spec for spec in sets}

    def metadata_xml() -> str:
        parts = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">',
            "<edmx:DataServices>",
            '<Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="e_estoque">',
        ]
        edm_types = {
            FieldType.STRING: "Edm.String",
            FieldType.NUMBER: "Edm.Decimal",
            FieldType.INSTANT: "Edm.DateTimeOffset",
            FieldType.BOOLEAN: "Edm.Boolean",
            FieldType.UUID: "Edm.String",
        }
        for spec in sets:
            parts.append(f'<EntityType Name="{spec.name}">')
            parts.append('<Key><PropertyRef Name="Id"/></Key>')
            for field_name, fdef in spec.fields.items():
                nullable = "" if field_name == "id" else ' Nullable="true"'
                parts.append(
                    f'<Property Name="{_pascal(field_name)}" '
                    f'Type="{edm_types[fdef.type]}"{nullable}/>'
                )
            parts.append("</EntityType>")
        parts.append("<EntityContainer Name='Container'>")
        for spec in sets:
            parts.append(f'<EntitySet Name="{spec.name}" EntityType="e_estoque.{spec.name}"/>')
        parts.append("</EntityContainer></Schema></edmx:DataServices></edmx:Edmx>")
        return "\n".join(parts)

    async def query_set(
        session: AsyncSession,
        spec: EntitySetSpec,
        filter_text: str | None,
        order_by: str | None,
        top: int | None,
        skip: int | None,
        count: bool,
        selected: list[str] | None,
    ) -> dict[str, Any]:
        stmt: Select[tuple[Any]] = select(spec.model)
        where = build_odata_filter(filter_text, spec.model, spec.fields)
        if where is not None:
            stmt = stmt.where(where)
        effective_top = min(top if top is not None else MAX_TOP, MAX_TOP)
        total = await count_rows(session, stmt) if count else None
        stmt = stmt.order_by(*order_columns(order_by, spec.model, spec.fields))
        if skip:
            stmt = stmt.offset(skip)
        rows = await page_rows(session, stmt, 1, max(effective_top, 1))
        columns = selected if selected else list(spec.columns)
        result: dict[str, Any] = {
            "@odata.context": f"$metadata#{spec.name}",
            "value": [_model_to_dict(row[0], columns) for row in rows],
        }
        if total is not None:
            result["@odata.count"] = total
        return result

    async def _entity_by_key_inner(
        session: AsyncSession, spec: EntitySetSpec, raw_key: str
    ) -> dict[str, Any]:
        key = raw_key.strip()
        # Literal tipado do OData: guid'xxxxxxxx-...'
        if key.lower().startswith("guid'") and key.endswith("'"):
            key = key[5:-1]
        key_condition = Condition(field="id", operator=Operator.EQ, value=key)
        stmt: Select[tuple[Any]] = select(spec.model)
        try:
            where = build_filter(key_condition, spec.model, spec.fields)
        except ValidationError:
            # Chave malformada (ex.: não-UUID) → recurso não encontrado (paridade .NET).
            raise NotFoundError("Not found") from None
        if where is not None:
            stmt = stmt.where(where)
        row = await first_row(session, stmt)
        if row is None:
            raise NotFoundError("Not found")
        return {
            "@odata.context": f"$metadata#{spec.name}/$entity",
            **_model_to_dict(row[0], list(spec.columns)),
        }

    for spec in sets:
        spec_ref = spec

        @router.get(f"/{spec_ref.name}/$count")
        async def entity_count(
            session: Annotated[AsyncSession, Depends(open_session)],
            spec: EntitySetSpec = spec_ref,
        ) -> Response:
            total = await count_rows(session, select(spec.model))
            return Response(content=str(total), media_type="text/plain")

        @router.get(f"/{spec_ref.name}")
        async def entity_set(
            session: Annotated[AsyncSession, Depends(open_session)],
            filter: str | None = None,  # noqa: A002 - nome OData
            orderby: Annotated[str | None, Query(alias="$orderby")] = None,
            top: Annotated[int | None, Query(alias="$top", ge=0)] = None,
            skip: Annotated[int | None, Query(alias="$skip", ge=0)] = None,
            count: Annotated[bool, Query(alias="$count")] = False,
            select_param: Annotated[str | None, Query(alias="$select")] = None,
            dollar_filter: Annotated[str | None, Query(alias="$filter")] = None,
            spec: EntitySetSpec = spec_ref,
        ) -> dict[str, Any]:
            selected = (
                [_pascal(part.strip()) for part in select_param.split(",")]
                if select_param
                else None
            )
            return await query_set(
                session, spec, dollar_filter or filter, orderby, top, skip, count, selected
            )

        @router.get(f"/{spec_ref.name}/{{key}}")
        async def entity_by_key(
            key: str,
            session: Annotated[AsyncSession, Depends(open_session)],
            spec: EntitySetSpec = spec_ref,
        ) -> dict[str, Any]:
            return await _entity_by_key_inner(session, spec, key)

    @router.get("/$metadata")
    async def metadata() -> Response:
        return Response(content=metadata_xml(), media_type="application/xml")

    @router.get("/{set_with_key:path}")
    async def entity_key_parenthesized(
        set_with_key: str,
        session: Annotated[AsyncSession, Depends(open_session)],
    ) -> dict[str, Any]:
        """Convenção OData v4: `Set(key)` (ex.: /odata/Products(guid'...'))."""
        match = _KEY_PATH.fullmatch(set_with_key)
        if match is None:
            raise NotFoundError("Not found")
        spec = by_name.get(match.group(1))
        if spec is None:
            raise NotFoundError("Not found")
        return await _entity_by_key_inner(session, spec, match.group(2))

    return router
