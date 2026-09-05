"""Regras de domínio Category: mensagens idênticas ao CategoryValidation .NET."""

from __future__ import annotations

from e_estoque.product.domain.category import Category, CategoryCreated, CategoryUpdated


def _valid() -> Category:
    return Category.create(
        name="Bebidas", description="Refrigerantes e sucos", short_description="Geladas"
    )


def test_create_valid_generates_id_and_event() -> None:
    category = _valid()
    assert category.is_valid
    assert category.id is not None
    assert category.created_at.tzinfo is not None
    events = category.pull_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, CategoryCreated)
    assert event.id == category.id
    assert event.name == "Bebidas"
    assert event.short_description == "Geladas"


def test_create_invalid_empty_name_messages() -> None:
    category = Category.create(name="", description="doc", short_description="short")
    assert not category.is_valid
    # Paridade FluentValidation: NotEmpty e Length falham → 2 mensagens na ordem das regras.
    assert category.errors == [
        "The Name needs to be provided",
        "The Name need to have between 3 and 80 characters",
    ]


def test_create_invalid_name_too_long() -> None:
    category = Category.create(name="x" * 81, description="doc", short_description="short")
    assert category.errors == ["The Name need to have between 3 and 80 characters"]


def test_description_and_short_description_limits() -> None:
    category = Category.create(name="Nome", description="d", short_description="s")
    # Ordem das regras .NET: Name → ShortDescription → Description.
    assert category.errors == [
        "The ShortDescription need to have between 3 and 500 characters",
        "The Description need to have between 3 and 5000 characters",
    ]


def test_short_description_max_500() -> None:
    category = Category.create(name="Nome", description="desc", short_description="s" * 501)
    assert "The ShortDescription need to have between 3 and 500 characters" in category.errors


def test_update_sets_updated_at_and_event() -> None:
    category = _valid()
    category.pull_events()
    category.update(name="Nome novo", description="Nova descrição", short_description="Novo")
    assert category.updated_at is not None
    events = category.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], CategoryUpdated)
    assert events[0].name == "Nome novo"


def test_update_invalid_marks_invalid() -> None:
    category = _valid()
    category.update(name="ab", description="Nova descrição", short_description="Novo")
    assert not category.is_valid


def test_soft_delete_lifecycle() -> None:
    category = _valid()
    now = category.created_at
    category.disable(now)
    assert category.is_deleted
    assert category.deleted_at == now
    category.activate()
    assert not category.is_deleted
    assert category.deleted_at is None
