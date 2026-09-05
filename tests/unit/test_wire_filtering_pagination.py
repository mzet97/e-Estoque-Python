"""Wire format RabbitMQ, parsers Gridify/OData e paginação (paridade .NET)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from e_estoque.company.domain.company import Company, CompanyAddress
from e_estoque.shared.api.schemas import PagedResult, paged_search_bounds
from e_estoque.shared.application.filtering import (
    And,
    Condition,
    Operator,
    parse_gridify_filter,
    parse_odata_filter,
    parse_order_by,
)
from e_estoque.shared.domain.entity import DomainEvent
from e_estoque.shared.domain.errors import ValidationError
from e_estoque.shared.domain.notifications import (
    ErrorNotification,
    LoginUserNotification,
    NotificationError,
)
from e_estoque.shared.infrastructure.messaging.wire import (
    event_payload,
    routing_key,
    serialize_event,
)


def _company() -> Company:
    return Company.create(
        name="Acme",
        doc_id="12345678",
        email="a@b.com",
        description="desc",
        phone_number="1199",
        company_address=CompanyAddress(
            street="Rua",
            number="1",
            complement="C",
            neighborhood="N",
            district="D",
            city="Ci",
            country="Co",
            zip_code="Z",
            latitude="La",
            longitude="Lo",
        ),
    )


def test_event_payload_camel_case_and_nested() -> None:
    event = _company().pull_events()[0]
    payload = event_payload(event)
    assert payload["docId"] == "12345678"
    assert payload["phoneNumber"] == "1199"
    assert payload["companyAddress"]["zipCode"] == "Z"
    assert "occurredOn" in payload


@dataclass(frozen=True, slots=True)
class WithDecimal(DomainEvent):
    price: Decimal
    occurred_on: datetime = field(default_factory=lambda: datetime.now(UTC))


def test_decimal_serializes_as_number() -> None:
    payload: dict[str, Any] = event_payload(WithDecimal(price=Decimal("9.50")))
    assert payload["price"] == 9.5
    assert isinstance(payload["price"], float)
    payload_int: dict[str, Any] = event_payload(WithDecimal(price=Decimal("10")))
    assert payload_int["price"] == 10
    assert isinstance(payload_int["price"], int)


def test_routing_key_dash_case() -> None:
    assert routing_key(NotificationError(event_name="a", description="b")) == "notification-error"
    assert routing_key(ErrorNotification(message="m")) == "error-notification"
    assert routing_key(LoginUserNotification(username="u")) == "login-user-notification"


def test_serialize_event_none_omitted() -> None:
    assert serialize_event(LoginUserNotification(username="u")) == '{"username":"u"}'


# ---- Gridify parser ----
def test_gridify_conditions() -> None:
    node = parse_gridify_filter("name^=jo&createdAt>2026-01-01")
    assert isinstance(node, And)
    first, second = node.children
    assert isinstance(first, Condition) and first.operator is Operator.STARTS_WITH
    assert first.value == "jo"
    assert isinstance(second, Condition) and second.operator is Operator.GT


def test_gridify_contains_star_value() -> None:
    node = parse_gridify_filter("name=*john*")
    assert isinstance(node, Condition)
    assert node.operator is Operator.CONTAINS
    assert node.value == "john"


def test_gridify_or_groups() -> None:
    node = parse_gridify_filter("name=bob|age>18")
    children = node.children if hasattr(node, "children") else []
    assert len(children) == 2


def test_gridify_invalid_raises() -> None:
    with pytest.raises(ValidationError):
        parse_gridify_filter("semoperador")


def test_gridify_quotes_and_pipe() -> None:
    node = parse_gridify_filter("name='a|b'")
    assert isinstance(node, Condition)
    assert node.value == "a|b"


def test_gridify_empty_returns_none() -> None:
    assert parse_gridify_filter(None) is None
    assert parse_gridify_filter("  ") is None


# ---- OData parser ----
def test_odata_parse_eq_and_contains() -> None:
    node = parse_odata_filter("name eq 'refri' and contains(description,'gel')")
    assert isinstance(node, And)
    left, right = node.children
    assert isinstance(left, Condition) and left.operator is Operator.EQ
    assert left.field == "name"
    assert isinstance(right, Condition) and right.operator is Operator.CONTAINS


def test_odata_parse_or() -> None:
    node = parse_odata_filter("startswith(name,'A') or price gt 10")
    assert hasattr(node, "children")
    children = node.children  # type: ignore[union-attr]
    assert len(children) == 2


def test_odata_unsupported_operator_raises() -> None:
    with pytest.raises(ValidationError):
        parse_odata_filter("name lol 'x'")


def test_parse_order_by() -> None:
    terms = parse_order_by("name asc, createdAt desc")
    assert terms[0].field == "name" and not terms[0].descending
    assert terms[1].field == "createdAt" and terms[1].descending
    assert parse_order_by(None) == []


# ---- Paginação (PagedResult .NET) ----
def test_paged_result_math() -> None:
    paged = PagedResult.create(current_page=2, page_size=10, row_count=42)
    assert paged.page_count == 5
    assert paged.first_row_on_page == 11
    assert paged.last_row_on_page == 20
    assert paged.skip == 10


def test_paged_result_empty_page() -> None:
    paged = PagedResult.create(current_page=1, page_size=25, row_count=0)
    assert paged.page_count == 0
    assert paged.last_row_on_page == 0


def test_paged_search_bounds_defaults_and_validation() -> None:
    assert paged_search_bounds(None, None) == (1, 10)
    assert paged_search_bounds(3, 50) == (3, 50)
    with pytest.raises(ValidationError):
        paged_search_bounds(0, None)
    with pytest.raises(ValidationError):
        paged_search_bounds(None, -1)
