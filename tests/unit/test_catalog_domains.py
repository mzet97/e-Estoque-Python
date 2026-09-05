"""Domínio Product/Inventory/Tax/Sale: invariantes e eventos (paridade .NET)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from e_estoque.inventory.domain.inventory import Inventory
from e_estoque.product.domain.product import Product, ProductCreated
from e_estoque.sale.domain.sale import PaymentType, Sale, SaleType
from e_estoque.tax.domain.tax import Tax


def _product_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": "Coca-Cola 2L",
        "description": "Refrigerante garrafa 2 litros",
        "short_description": "Coca 2L",
        "price": Decimal("9.99"),
        "weight": Decimal("2.1"),
        "height": Decimal("32"),
        "length": Decimal("11"),
        "image": "https://example.com/coca.png",
        "id_category": uuid4(),
        "id_company": uuid4(),
    }
    base.update(overrides)
    return base


def test_product_create_valid_event_without_image() -> None:
    product = Product.create(**_product_kwargs())  # type: ignore[arg-type]
    assert product.is_valid
    event = product.pull_events()[0]
    assert isinstance(event, ProductCreated)
    # Paridade do .NET: ProductCreated NÃO carrega Image.
    assert not hasattr(event, "image")


def test_product_decimal_rules() -> None:
    product = Product.create(**_product_kwargs(price=Decimal("0")))  # type: ignore[arg-type]
    assert product.errors == [
        "The Price needs to be provided",
        "The Price need to be greater 0",
    ]


def test_product_updated_event_drops_image() -> None:
    product = Product.create(**_product_kwargs())  # type: ignore[arg-type]
    product.pull_events()
    product.update(**_product_kwargs(image="https://example.com/nova.png"))  # type: ignore[arg-type]
    event = product.pull_events()[0]
    assert not hasattr(event, "image")


def test_inventory_quantity_must_be_positive() -> None:
    inventory = Inventory.create(quantity=0, date_order=datetime.now(UTC), id_product=uuid4())
    assert inventory.errors == [
        "The Quantity needs to be provided",
        "The Quantity needs to be greater than 0",
    ]


def test_tax_percentage_range() -> None:
    tax = Tax.create(
        name="ICMS",
        description="Imposto circulacao",
        percentage=Decimal("101"),
        id_category=uuid4(),
    )
    assert tax.errors == ["The Percentage need to be between 0 and 100"]


def test_sale_total_tax_zero_is_invalid_parity() -> None:
    sale = Sale.create(
        quantity=2,
        total_price=Decimal("19.98"),
        total_tax=Decimal("0"),
        sale_type=SaleType.UNITARY,
        payment_type=PaymentType.PIX,
        delivery_date=datetime(2026, 9, 10, tzinfo=UTC),
        sale_date=datetime(2026, 9, 4, tzinfo=UTC),
        payment_date=datetime(2026, 9, 4, tzinfo=UTC),
        id_customer=uuid4(),
        ids_products=[uuid4()],
    )
    assert "The TotalTax needs to be greater than 0" in sale.errors


def test_sale_creates_one_line_per_product_with_sale_quantity() -> None:
    ids = [uuid4(), uuid4(), uuid4()]
    sale = Sale.create(
        quantity=5,
        total_price=Decimal("50"),
        total_tax=Decimal("5"),
        sale_type=SaleType.RECURRENT,
        payment_type=PaymentType.CREDIT_CARD,
        delivery_date=datetime(2026, 9, 10, tzinfo=UTC),
        sale_date=datetime(2026, 9, 4, tzinfo=UTC),
        payment_date=datetime(2026, 9, 5, tzinfo=UTC),
        id_customer=uuid4(),
        ids_products=ids,
    )
    assert len(sale.sale_products) == 3
    assert [line.id_product for line in sale.sale_products] == ids
    assert all(line.quantity == 5 for line in sale.sale_products)
    assert all(line.id_sale == sale.id for line in sale.sale_products)


def test_sale_enum_parse_fallback_parity() -> None:
    # Helpers .NET: parse inválido cai em Unitary/PIX.
    assert SaleType.from_string("xpto") is SaleType.UNITARY
    assert SaleType.from_string("recurrent") is SaleType.RECURRENT
    assert PaymentType.from_string("xpto") is PaymentType.PIX
    assert PaymentType.from_string("creditcard") is PaymentType.CREDIT_CARD
