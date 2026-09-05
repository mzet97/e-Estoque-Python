"""Verificações de invariantes com as mensagens exatas do .NET (FluentValidation).

Semânticas preservadas:
- "NotEmpty" em números: falha quando o valor é o default (zero).
- "Length": não falha para None (o NotEmpty da regra anterior cobre).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

MIN_DATE = datetime(1900, 1, 1)
MAX_DATE = datetime(3000, 12, 31)


def _dt(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value.tzinfo else value


def audit(
    id: UUID | None,
    created_at: datetime | None,
    updated_at: datetime | None,
    deleted_at: datetime | None,
    errors: list[str],
) -> None:
    """EntityValidation: id e datas de auditoria."""
    if id is None:
        errors.append("The Id cannot be empty.")
    if created_at is None:
        errors.append("The creation date must be provided.")
    elif not (MIN_DATE <= _dt(created_at) <= MAX_DATE):
        errors.append("The creation date must be between 1900 and 3000.")
    for date, prop in ((updated_at, "UpdatedAt"), (deleted_at, "DeletedAt")):
        if date is not None and not (MIN_DATE <= _dt(date) <= MAX_DATE):
            errors.append(f"{prop} must be a valid date between 1900 and 3000 or null.")


def provided(errors: list[str], value: Any, prop: str) -> None:
    """'The {Prop} needs to be provided' — string/enum/uuid/instant/objeto."""
    if value is None or (isinstance(value, str) and not value.strip()):
        errors.append(f"The {prop} needs to be provided")


def provided_number(errors: list[str], value: Any, prop: str) -> None:
    """NotEmpty numérico: falha quando o valor é default (zero)."""
    if value is None or value == 0:
        errors.append(f"The {prop} needs to be provided")


def required(errors: list[str], value: Any, prop: str) -> None:
    """'{Prop} is required' — string/objeto (estilo Company/Customer)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        errors.append(f"{prop} is required")


def length(errors: list[str], value: str | None, prop: str, minimum: int, maximum: int) -> None:
    if value is not None and not (minimum <= len(value) <= maximum):
        errors.append(f"The {prop} need to have between {minimum} and {maximum} characters")


def positive(errors: list[str], value: int | None, prop: str) -> None:
    """'The {Prop} needs to be greater than 0' — inteiro."""
    if value is not None and value <= 0:
        errors.append(f"The {prop} needs to be greater than 0")


def positive_decimal(errors: list[str], value: Decimal | None, prop: str) -> None:
    """'The {Prop} need to be greater 0' — decimal (mensagem do ProductValidation)."""
    if value is not None and value <= 0:
        errors.append(f"The {prop} need to be greater 0")


def inclusive_range(
    errors: list[str], value: Decimal | None, prop: str, minimum: int, maximum: int
) -> None:
    if value is not None and not (Decimal(minimum) <= value <= Decimal(maximum)):
        errors.append(f"The {prop} need to be between {minimum} and {maximum}")


def not_empty_guid(errors: list[str], value: UUID | None, prop: str) -> None:
    if value is None:
        errors.append(f"The {prop} cannot be empty.")


def when(invalid: bool, message: str, errors: list[str]) -> None:
    if invalid:
        errors.append(message)
