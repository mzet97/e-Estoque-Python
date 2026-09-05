"""Observabilidade: métricas Prometheus em /metrics + OTel opcional (ADR-012).

HTTP via `prometheus-fastapi-instrumentator` (requests, latência, status — labels
por template de rota, sem alta cardinalidade; namespace `e_estoque`). Contador de
publicações no broker fica no registro default, junto das métricas HTTP.
Tracing OpenTelemetry é opcional (extra `otel`), exportando via OTLP gRPC.
"""

from __future__ import annotations

from prometheus_client import Counter
from starlette.applications import Starlette

BUS_PUBLISHED = Counter(
    "e_estoque_bus_published_total",
    "Domain events published to the message bus",
    ("exchange", "outcome"),
)


def note_bus_publish(exchange: str, outcome: str) -> None:
    """Registra resultado de um publish (ok/fail) — chamado pelo DirectMessageBus."""
    BUS_PUBLISHED.labels(exchange=exchange, outcome=outcome).inc()


def init_metrics(app: Starlette) -> None:
    """Instrumenta o app e expõe `/metrics` (padrão Prometheus do .NET)."""
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator(should_group_status_codes=True).instrument(
        app, metric_namespace="e_estoque"
    ).expose(app, endpoint="/metrics", include_in_schema=False)


def init_tracing(app: object, otlp_endpoint: str | None, engine: object | None = None) -> None:
    """OTel opcional (extra `otel`): FastAPI/HTTP/SQLAlchemy → OTLP gRPC."""
    if not otlp_endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return
    provider = TracerProvider(
        resource=Resource.create({"service.name": "E-estoque", "service.version": "1"})
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    if engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=engine)
