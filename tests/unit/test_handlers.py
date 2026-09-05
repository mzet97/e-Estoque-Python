"""Handlers de aplicação com repositórios/bus falsos (regras e mensagens .NET)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from e_estoque.company.application.company_handlers import (
    AddressInput,
    CreateCompanyCommand,
    CreateCompanyHandler,
)
from e_estoque.company.domain.company import Company, CompanyRepository
from e_estoque.customer.application.customer_handlers import (
    DeleteCustomerCommand,
    DeleteCustomerHandler,
)
from e_estoque.customer.domain.customer import Customer, CustomerAddress, CustomerRepository
from e_estoque.product.application.product_handlers import (
    CreateProductCommand,
    CreateProductHandler,
)
from e_estoque.sale.application.sale_handlers import (
    CreateSaleCommand,
    CreateSaleHandler,
    DeleteSaleCommand,
    DeleteSaleHandler,
)
from e_estoque.shared.domain.errors import NotFoundError, ValidationError
from e_estoque.shared.domain.search import SearchResult
from e_estoque.shared.infrastructure.db import UnitOfWork
from e_estoque.tax.application.tax_handlers import CreateTaxCommand, CreateTaxHandler

ADDRESS = AddressInput(
    street="Rua das Flores",
    number="123",
    complement="Sala 2",
    neighborhood="Centro",
    district="Centro",
    city="São Paulo",
    country="Brasil",
    zip_code="01310-000",
    latitude="-23.55",
    longitude="-46.63",
)


class FakeBus:
    def __init__(self) -> None:
        self.published: list[tuple[object, str]] = []
        self.errors: list[tuple[str, str, str]] = []
        self.notifications: list[object] = []

    async def publish(self, event: object, exchange: str) -> None:
        self.published.append((event, exchange))

    async def publish_notification_error(
        self, event_name: str, description: str, exchange: str
    ) -> None:
        self.errors.append((event_name, description, exchange))

    async def publish_error_notification(self, notification: object) -> None:
        self.notifications.append(notification)

    async def publish_login_notification(self, notification: object) -> None:
        self.notifications.append(notification)


class FakeUow(UnitOfWork):
    def __init__(self, session: object = None) -> None:  # type: ignore[no-untyped-def]
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None


def make_repo(entity_name: str, existing: object | None = None) -> object:
    """Repositório falso em memória com a porta mínima usada pelos handlers."""

    class FakeCompanyRepository(CompanyRepository):
        def __init__(self) -> None:
            self.saved: list[Company] = []

        async def save(self, company: Company) -> None:
            self.saved.append(company)

        async def find_by_id(self, company_id: UUID) -> Company | None:
            return existing if isinstance(existing, Company) else None

        async def exists(self, company_id: UUID) -> bool:
            return bool(existing)

        async def search(self, criteria: object) -> SearchResult[Company]:
            return SearchResult(data=[], row_count=0, page=1, size=10)

        async def search_gridify(
            self, filter_text: str | None, order_text: str | None, page: int, size: int
        ) -> SearchResult[Company]:
            return SearchResult(data=[], row_count=0, page=page, size=size)

        async def delete_hard(self, company_id: UUID) -> None:
            return None

    if entity_name == "company":
        return FakeCompanyRepository()
    raise AssertionError(entity_name)


async def test_create_company_invalid_publishes_notification_and_raises_400() -> None:
    repo: object = make_repo("company")
    bus = FakeBus()
    uow = FakeUow()  # type: ignore[arg-type]
    handler = CreateCompanyHandler(repo, uow, bus)  # type: ignore[arg-type]
    command = CreateCompanyCommand(
        name="ab",
        doc_id="",
        email="a@b.com",
        description="desc",
        phone_number="1199",
        company_address=ADDRESS,
    )
    with pytest.raises(ValidationError) as excinfo:
        await handler.handle(command)
    # 400: mensagens de validação unidas por vírgula (paridade .NET).
    assert "The Name need to have between 3 and 80 characters" in str(excinfo.value)
    assert bus.errors and bus.errors[0][0] == "Validate Company has error"
    assert uow.commits == 0


async def test_create_company_valid_commits_and_publishes_event() -> None:
    repo = make_repo("company")
    bus = FakeBus()
    uow = FakeUow()  # type: ignore[arg-type]
    handler = CreateCompanyHandler(repo, uow, bus)  # type: ignore[arg-type]
    command = CreateCompanyCommand(
        name="Acme Ltda",
        doc_id="12345678000190",
        email="a@acme.com",
        description="Indústria de base",
        phone_number="11940028922",
        company_address=ADDRESS,
    )
    company_id = await handler.handle(command)
    assert isinstance(company_id, UUID)
    assert uow.commits == 1
    assert len(bus.published) == 1
    event, exchange = bus.published[0]
    assert exchange == "company-service"
    assert type(event).__name__ == "CompanyCreated"


class FakeCompanyReader:
    def __init__(self, exists: bool) -> None:
        self._exists = exists

    async def exists(self, category_id: UUID) -> bool:
        return self._exists


class FakeProductRepo:
    async def save(self, product: object) -> None:
        return None

    async def find_by_id(self, product_id: UUID) -> None:
        return None

    async def exists(self, product_id: UUID) -> bool:
        return True

    async def find_detailed_by_id(self, product_id: UUID) -> None:
        return None

    async def search(self, criteria: object) -> SearchResult:
        return SearchResult(data=[], row_count=0, page=1, size=10)

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult:
        return SearchResult(data=[], row_count=0, page=page, size=size)

    async def delete_hard(self, product_id: UUID) -> None:
        return None


async def test_create_product_missing_company_raises_404() -> None:
    bus = FakeBus()
    handler = CreateProductHandler(
        FakeProductRepo(),
        FakeUow(),
        bus,  # type: ignore[arg-type]
        FakeCompanyReader(exists=True),
        FakeCompanyReader(exists=False),
    )
    command = CreateProductCommand(
        name="Coca 2L",
        description="Refrigerante 2 litros",
        short_description="Coca 2L",
        price=Decimal("9.99"),
        weight=Decimal("2.1"),
        height=Decimal("32"),
        length=Decimal("11"),
        image="https://example.com/coca.png",
        id_category=uuid4(),
        id_company=uuid4(),
    )
    with pytest.raises(NotFoundError) as excinfo:
        await handler.handle(command)
    assert str(excinfo.value) == "Company not found"
    assert bus.errors[0][0] == "Company not found"


async def test_create_tax_missing_category_raises_400_parity() -> None:
    bus = FakeBus()

    class FakeTaxRepo:
        async def save(self, tax: object) -> None:
            return None

        async def find_by_id(self, tax_id: UUID) -> None:
            return None

        async def find_detailed_by_id(self, tax_id: UUID) -> None:
            return None

        async def search(self, criteria: object) -> SearchResult:
            return SearchResult(data=[], row_count=0, page=1, size=10)

        async def search_gridify(
            self, filter_text: str | None, order_text: str | None, page: int, size: int
        ) -> SearchResult:
            return SearchResult(data=[], row_count=0, page=page, size=size)

        async def delete_hard(self, tax_id: UUID) -> None:
            return None

    handler = CreateTaxHandler(
        FakeTaxRepo(),
        FakeUow(),
        bus,  # type: ignore[arg-type]
        FakeCompanyReader(exists=False),
    )
    command = CreateTaxCommand(
        name="ICMS",
        description="Imposto sobre circulação",
        percentage=Decimal("18"),
        id_category=uuid4(),
    )
    # Paridade do .NET: Tax usa ValidationException (400), não NotFound (404).
    with pytest.raises(ValidationError) as excinfo:
        await handler.handle(command)
    assert str(excinfo.value) == "Category not found"


def _customer() -> Customer:
    return Customer.create(
        name="Maria Silva",
        doc_id="12345678901",
        email="maria@x.com",
        description="Cliente",
        phone_number="1199999999",
        customer_address=CustomerAddress(
            street="Rua",
            number="12",
            complement="C",
            neighborhood="N",
            district="D",
            city="Ci",
            country="Co",
            zip_code="Zip",
            latitude="Lat",
            longitude="Lon",
        ),
    )


class FakeCustomerRepository(CustomerRepository):
    def __init__(self, existing: Customer | None) -> None:
        self._existing = existing
        self.disabled: UUID | None = None

    async def save(self, customer: Customer) -> None:
        return None

    async def find_by_id(self, customer_id: UUID) -> Customer | None:
        return self._existing

    async def exists(self, customer_id: UUID) -> bool:
        return self._existing is not None

    async def search(self, criteria: object) -> SearchResult[Customer]:
        return SearchResult(data=[], row_count=0, page=1, size=10)

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult[Customer]:
        return SearchResult(data=[], row_count=0, page=page, size=size)

    async def disable(self, customer_id: UUID, now: datetime) -> bool:
        self.disabled = customer_id
        return self._existing is not None


async def test_delete_customer_is_soft_parity() -> None:
    bus = FakeBus()
    repo = FakeCustomerRepository(existing=_customer())
    handler = DeleteCustomerHandler(repo, FakeUow(), bus)  # type: ignore[arg-type]
    await handler.handle(DeleteCustomerCommand(id=uuid4()))
    assert repo.disabled is not None  # soft delete, sem delete_hard


async def test_delete_customer_missing_raises_404() -> None:
    bus = FakeBus()
    repo: CustomerRepository = FakeCustomerRepository(existing=None)
    handler = DeleteCustomerHandler(repo, FakeUow(), bus)  # type: ignore[arg-type]
    with pytest.raises(NotFoundError):
        await handler.handle(DeleteCustomerCommand(id=uuid4()))
    assert bus.errors[0][0] == "Delete Customer has error"


class FakeSaleRepository:
    def __init__(self, existing: bool) -> None:
        self._existing = existing
        self.disabled: UUID | None = None

    async def save(self, sale: object) -> None:
        return None

    async def find_by_id(self, sale_id: UUID) -> None:
        return None

    async def find_detailed_by_id(self, sale_id: UUID) -> None:
        return None

    async def search(self, criteria: object) -> SearchResult:
        return SearchResult(data=[], row_count=0, page=1, size=10)

    async def search_gridify(
        self, filter_text: str | None, order_text: str | None, page: int, size: int
    ) -> SearchResult:
        return SearchResult(data=[], row_count=0, page=page, size=size)

    async def disable(self, sale_id: UUID, now: datetime) -> bool:
        self.disabled = sale_id
        return self._existing


async def test_delete_sale_is_soft_parity() -> None:
    bus = FakeBus()
    repo = FakeSaleRepository(existing=True)
    handler = DeleteSaleHandler(repo, FakeUow(), bus)  # type: ignore[arg-type]
    sale_id = uuid4()
    await handler.handle(DeleteSaleCommand(id=sale_id))
    assert repo.disabled == sale_id


async def test_create_sale_missing_product_raises_404() -> None:
    class MissingProductReader:
        async def exists(self, product_id: UUID) -> bool:
            return False

    bus = FakeBus()
    handler = CreateSaleHandler(
        FakeSaleRepository(existing=True),
        FakeUow(),
        bus,  # type: ignore[arg-type]
        FakeCompanyReader(exists=True),
        MissingProductReader(),
    )
    command = CreateSaleCommand(
        quantity=1,
        total_price=Decimal("10"),
        total_tax=Decimal("1"),
        sale_type=1,
        payment_type=1,
        delivery_date=datetime(2026, 9, 10, tzinfo=UTC),
        sale_date=datetime(2026, 9, 4, tzinfo=UTC),
        payment_date=datetime(2026, 9, 4, tzinfo=UTC),
        id_customer=uuid4(),
        ids_products=[uuid4()],
    )
    with pytest.raises(NotFoundError):
        await handler.handle(command)
    assert bus.errors[0][0] == "Product not found"
