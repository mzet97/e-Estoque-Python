"""AddressInput compartilhado (payload de endereço de Company/Customer)."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class AddressInput:
    """Campos do value object de endereço no contrato HTTP."""

    street: str
    number: str
    complement: str
    neighborhood: str
    district: str
    city: str
    country: str
    zip_code: str
    latitude: str
    longitude: str

    def to_vo(self, vo_type: type[T]) -> T:
        return vo_type(**dataclasses.asdict(self))
