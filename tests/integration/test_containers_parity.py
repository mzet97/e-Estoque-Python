"""Integração real com PostgreSQL/RabbitMQ via Testcontainers.

Requer Docker. Sem Docker os testes são PULADOS explicitamente (o ambiente
local não tem Docker; o CI executa com service containers).
Paridade de schema: migration Alembic 0001 == schema EF 20250327000516_001.
"""

from __future__ import annotations

import os

import pytest


def _docker_available() -> bool:
    """Sondagem de ambiente: Docker daemon acessível?"""
    try:
        import docker  # type: ignore[import-not-found]

        docker.from_env().ping()
    except Exception:  # noqa: BLE001
        return False
    return True


pytestmark = pytest.mark.skipif(
    os.environ.get("EESTOQUE_SKIP_DOCKER", "1") == "1" or not _docker_available(),
    reason="requer Docker (defina EESTOQUE_SKIP_DOCKER=0 com Docker ativo)",
)


def test_postgres_schema_parity() -> None:  # pragma: no cover - requer Docker
    """Aplica a migration 0001 em PostgreSQL 17 e confere tabelas/FKs/indexes."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:17") as postgres:
        import sqlalchemy

        url = postgres.get_connection_url().replace("+psycopg2", "+asyncpg")
        engine = sqlalchemy.create_engine(url.replace("+asyncpg", ""))
        with engine.begin() as connection:
            from alembic import command
            from alembic.config import Config

            root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            config = Config(os.path.join(root, "alembic.ini"))
            config.set_main_option("sqlalchemy.url", url)
            command.upgrade(config, "head")

            tables = {
                row[0]
                for row in connection.execute(
                    sqlalchemy.text(
                        "SELECT table_name FROM information_schema.tables"
                        " WHERE table_schema='public'"
                    )
                )
            }
            expected = {
                "Categories",
                "Companies",
                "Customers",
                "Products",
                "inventories",
                "Sales",
                "SaleProducts",
                "Taxs",
            }
            assert expected <= tables

            fks = {
                row[0]
                for row in connection.execute(
                    sqlalchemy.text(
                        "SELECT constraint_name FROM information_schema.table_constraints"
                        " WHERE constraint_type='FOREIGN KEY' AND table_schema='public'"
                    )
                )
            }
            assert "FK_Products_Categories_IdCategory" in fks
            assert "FK_SaleProducts_Sales_IdSale" in fks

            indexes = {
                row[0]
                for row in connection.execute(
                    sqlalchemy.text("SELECT indexname FROM pg_indexes WHERE schemaname='public'")
                )
            }
            assert "IX_Products_IdCategory" in indexes
            assert "IX_Taxs_IdCategory" in indexes


def test_rabbitmq_publish_declares_exchanges() -> None:  # pragma: no cover - requer Docker
    from testcontainers.rabbitmq import RabbitMqContainer

    with RabbitMqContainer("rabbitmq:3.13-management") as rabbit:
        import asyncio

        from e_estoque.shared.infrastructure.messaging.rabbit import RabbitPublisher

        publisher = RabbitPublisher(
            host=rabbit.get_container_host_ip(),
            port=int(rabbit.get_exposed_port(5672)),
            username=rabbit.username,
            password=rabbit.password,
        )

        async def flow() -> None:
            await publisher.connect()
            await publisher.publish_raw(
                b'{"username":"t"}', "noticiation-service", "login-user-notification"
            )
            await publisher.close()

        asyncio.run(flow())
