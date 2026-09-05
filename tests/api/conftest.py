"""Fixtures da suíte de API: app testing + SQLite em memória + bus fake.

Paridade do env Testing .NET: autenticação sempre bem-sucedida com roles
Create+User; RabbitMQ substituído (FakeBus). SQLite é usado APENAS para
comportamento de aplicação — paridade PostgreSQL fica em tests/integration.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from e_estoque.bootstrap.settings import Settings
from e_estoque.main import FakeBus, create_app
from e_estoque.shared.infrastructure.db import UnitOfWork, open_session, open_uow
from e_estoque.shared.infrastructure.registry import ALL_BASES


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as connection:
        for base in ALL_BASES:
            await connection.run_sync(base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def app(engine: AsyncEngine) -> AsyncIterator[object]:
    settings = Settings(environment="testing")
    application = create_app(settings)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_uow() -> AsyncIterator[UnitOfWork]:
        async with factory() as session:
            yield UnitOfWork(session)

    async def override_session() -> AsyncIterator[object]:
        async with factory() as session:
            yield session

    application.dependency_overrides[open_uow] = override_uow
    application.dependency_overrides[open_session] = override_session
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
async def bus(app: object) -> FakeBus:
    return app.state.bus  # type: ignore[union-attr]


@pytest.fixture
async def client(app: object) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
