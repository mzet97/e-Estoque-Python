"""Configurações (pydantic-settings) — nenhuma credencial no código."""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EESTOQUE_", env_file=".env", extra="ignore")

    app_name: str = "e-estoque-api"
    environment: str = "development"
    server_port: int = 8000

    database_url: SecretStr = SecretStr("postgresql+asyncpg://postgres:postgres@localhost:15432/e-estoque-py")
    db_echo: bool = False

    redis_host: str = "localhost"
    redis_port: int = 16379
    redis_password: SecretStr = SecretStr("")

    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 25671
    rabbitmq_username: str = "dsv"
    rabbitmq_password: SecretStr = SecretStr("dsv@123")

    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "e-estoque"
    keycloak_client_id: str = "e-estoque-client"
    keycloak_client_secret: SecretStr = SecretStr("")
    keycloak_issuer: str = "http://localhost:8080/realms/e-estoque"

    cors_origins: list[str] = ["*"]
    otlp_endpoint: str | None = None

    @property
    def sync_database_url(self) -> str:
        """URL síncrona (alembic)."""
        return self.database_url.get_secret_value().replace("+asyncpg", "")
