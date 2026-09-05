"""Validações de Company/Customer/Address (mensagens `{Prop} is required` do .NET)."""

from __future__ import annotations

from e_estoque.company.domain.company import Company, CompanyAddress
from e_estoque.customer.domain.customer import Customer, CustomerAddress


def _address() -> CompanyAddress:
    return CompanyAddress(
        street="Rua das Flores",
        number="123",
        complement="Sala 2",
        neighborhood="Centro",
        district="Distrito Industrial",
        city="São Paulo",
        country="Brasil",
        zip_code="01310-000",
        latitude="-23.5505",
        longitude="-46.6333",
    )


def _customer_address() -> CustomerAddress:
    addr = _address()
    return CustomerAddress(
        **{
            field: getattr(addr, field)
            for field in (
                "street",
                "number",
                "complement",
                "neighborhood",
                "district",
                "city",
                "country",
                "zip_code",
                "latitude",
                "longitude",
            )
        }
    )


def test_company_create_valid() -> None:
    company = Company.create(
        name="Acme Ltda",
        doc_id="12.345.678/0001-90",
        email="contato@acme.com",
        description="Indústria",
        phone_number="+55 11 4002-8922",
        company_address=_address(),
    )
    assert company.is_valid
    assert company.pull_events()[0].name == "Acme Ltda"  # CompanyCreated


def test_company_required_messages() -> None:
    company = Company.create(
        name="",
        doc_id="",
        email="",
        description="",
        phone_number="",
        company_address=None,  # type: ignore[arg-type]
    )
    # Cada RuleFor .NET dispara NotEmpty + Length (CascadeMode.Continue).
    for required_msg in (
        "Name is required",
        "DocId is required",
        "Email is required",
        "Description is required",
        "PhoneNumber is required",
        "CompanyAddress is required",
    ):
        assert required_msg in company.errors


def test_company_address_fields_required_and_longitude_not_validated() -> None:
    address = CompanyAddress(
        street="",
        number="1",
        complement="C",
        neighborhood="N",
        district="D",
        city="Ci",
        country="Co",
        zip_code="Z",
        latitude="La",
        longitude="",
    )
    company = Company.create(
        name="Acme",
        doc_id="12345678",
        email="a@b.com",
        description="desc",
        phone_number="1199",
        company_address=address,
    )
    # Paridade: Longitude não possui regra no .NET (nem NotEmpty, nem Length).
    assert not any("Longitude" in error for error in company.errors)
    assert "Street is required" in company.errors
    # "Ru" (não vazio) viola apenas Length — paridade do NotEmpty do FluentValidation.
    short = Company.create(
        name="Acme",
        doc_id="12345678",
        email="a@b.com",
        description="desc",
        phone_number="1199",
        company_address=CompanyAddress(
            street="Ru",
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
    assert "The Street need to have between 3 and 80 characters" in short.errors
    assert "Street is required" not in short.errors


def test_customer_email_limit_80_parity() -> None:
    customer = Customer.create(
        name="Maria Silva",
        doc_id="12345678901",
        email="m" * 81 + "@x.com",
        description="Cliente antigo",
        phone_number="1199999999",
        customer_address=_customer_address(),
    )
    assert "The Email need to have between 3 and 80 characters" in customer.errors


def test_customer_soft_delete() -> None:
    customer = Customer.create(
        name="Maria Silva",
        doc_id="12345678901",
        email="maria@x.com",
        description="Cliente",
        phone_number="1199999999",
        customer_address=_customer_address(),
    )
    customer.disable(customer.created_at)
    assert customer.is_deleted and customer.deleted_at is not None
