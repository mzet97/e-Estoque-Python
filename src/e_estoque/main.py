"""Composition root: create_app — wiring de settings, db, bus, auth, routers, obs."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from e_estoque.bootstrap.observability import (
    PrometheusMiddleware,
    init_tracing,
    metrics_endpoint,
)
from e_estoque.bootstrap.settings import Settings
from e_estoque.company.api.company_router import router as company_router
from e_estoque.customer.api.customer_router import router as customer_router
from e_estoque.filtering.odata import build_router as build_odata_router
from e_estoque.filtering.sets import odata_sets
from e_estoque.identity.api.auth_router import router as auth_router
from e_estoque.identity.application.keycloak_client import KeycloakClient
from e_estoque.inventory.api.inventory_router import router as inventory_router
from e_estoque.product.api.category_router import router as category_router
from e_estoque.product.api.product_router import router as product_router
from e_estoque.sale.api.sale_router import router as sale_router
from e_estoque.shared.api.error_handlers import install_exception_handlers
from e_estoque.shared.api.health import router as health_router
from e_estoque.shared.api.security import KeycloakValidator
from e_estoque.shared.infrastructure.db import dispose_engine, init_engine
from e_estoque.shared.infrastructure.messaging.bus import DirectMessageBus
from e_estoque.shared.infrastructure.messaging.rabbit import RabbitPublisher
from e_estoque.tax.api.tax_router import router as tax_router


class FakeBus:
    """Bus de teste/Testing env: registra publicações em memória."""

    def __init__(self) -> None:
        self.published: list[tuple[object, str]] = []
        self.errors: list[tuple[str, str, str]] = []

    async def publish(self, event: object, exchange: str) -> None:
        self.published.append((event, exchange))

    async def publish_notification_error(
        self, event_name: str, description: str, exchange: str
    ) -> None:
        self.errors.append((event_name, description, exchange))

    async def publish_error_notification(self, notification: object) -> None:
        self.published.append((notification, "noticiation-service"))

    async def publish_login_notification(self, notification: object) -> None:
        self.published.append((notification, "noticiation-service"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Abre engine + tracing fora do env Testing; fecha tudo no shutdown."""
    settings: Settings = app.state.settings
    if settings.environment != "testing":
        engine = init_engine(settings)
        init_tracing(app, settings.otlp_endpoint, engine)
    yield
    await dispose_engine()
    publisher: RabbitPublisher | None = getattr(app.state, "rabbit_publisher", None)
    if publisher is not None:
        try:
            await publisher.close()
        except Exception:  # noqa: BLE001 - shutdown tolerante
            pass


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    testing = settings.environment == "testing"

    app = FastAPI(
        title="E-estoque",
        version="1",
        docs_url=None if testing else "/docs",
        redoc_url=None if testing else "/redoc",
        openapi_url=None if testing else "/openapi.json",
        lifespan=lifespan,
    )

    # ---- estado compartilhado (composition root) ----
    app.state.settings = settings
    app.state.auth_disabled = testing  # equivalente ao TestAuthenticationHandler
    bus: FakeBus | DirectMessageBus
    if testing:
        # Paridade do env Testing .NET: broker ausente.
        bus = FakeBus()
    else:
        publisher = RabbitPublisher(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            username=settings.rabbitmq_username,
            password=settings.rabbitmq_password.get_secret_value(),
        )
        app.state.rabbit_publisher = publisher
        bus = DirectMessageBus(publisher)
    app.state.bus = bus
    app.state.keycloak_client = KeycloakClient(
        base_url=settings.keycloak_url,
        realm=settings.keycloak_realm,
        client_id=settings.keycloak_client_id,
        client_secret=settings.keycloak_client_secret.get_secret_value(),
        bus=bus,
    )
    if not testing:
        app.state.jwt_validator = KeycloakValidator(settings)

    # ---- cross-cutting ----
    install_exception_handlers(app)
    app.add_middleware(PrometheusMiddleware)

    # ---- routers ----
    app.include_router(auth_router)
    app.include_router(category_router)
    app.include_router(company_router)
    app.include_router(customer_router)
    app.include_router(inventory_router)
    app.include_router(product_router)
    app.include_router(sale_router)
    app.include_router(tax_router)
    app.include_router(health_router)
    app.include_router(build_odata_router(odata_sets()))
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)

    # ---- CORS (paridade CorsConfig.cs: Development allow-all / Production GET) ----
    from fastapi.middleware.cors import CORSMiddleware

    origins = settings.cors_origins
    allow_all = "*" in origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else origins,
        allow_methods=["*"] if allow_all else ["GET"],
        allow_headers=["*"],
        allow_credentials=False,
    )
    return app


app = create_app()
