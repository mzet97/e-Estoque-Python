"""Wire-format do broker, idêntico ao RabbitMqClient .NET: JSON camelCase, nulls omitidos."""

from __future__ import annotations

import dataclasses
import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID


def _to_camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(word.title() for word in rest)


def _serialize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, Decimal):
        # JsonSerializerDefaults.Web (.NET) emite decimal como número JSON.
        integral = value == value.to_integral_value()
        return int(value) if integral else float(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            _to_camel(k): _serialize(v)
            for k, v in dataclasses.asdict(value).items()
            if v is not None
        }
    if isinstance(value, dict):
        return {_to_camel(str(k)): _serialize(v) for k, v in value.items() if v is not None}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return str(value)


def event_payload(event: Any) -> dict[str, Any]:
    """Converte um dataclass de evento no dict camelCase (wire format .NET)."""
    result = _serialize(event)
    if not isinstance(result, dict):
        raise TypeError(f"Event must serialize to an object, got {type(result).__name__}")
    return result


def serialize_event(event: Any) -> str:
    """Serializa um dataclass de evento para o payload publicado."""
    return json.dumps(event_payload(event), ensure_ascii=False)


def to_dash_case(name: str) -> str:
    """Routing key = nome da classe em dash-case (ToDashCase do .NET)."""
    if not name:
        return name
    out = [name[0].lower()]
    for ch in name[1:]:
        if ch.isupper():
            out.append("-")
            out.append(ch.lower())
        else:
            out.append(ch)
    return "".join(out)


def routing_key(event: Any) -> str:
    return to_dash_case(type(event).__name__)
