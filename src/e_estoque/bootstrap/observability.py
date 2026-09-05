"""Observabilidade: métricas Prometheus em /metrics + OTel opcional (ADR-012).

Labels sem alta cardinalidade (método, rota, status) — nunca ids de usuário/entidade.
"""

from __future__ import annotations

import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

registry = CollectorRegistry(auto_describe=True)

HTTP_REQUESTS = Counter(
    "e_estoque_http_requests_total",
    "HTTP requests",
    ("method", "endpoint", "status"),
    registry=registry,
)
HTTP_LATENCY = Histogram(
    "e_estoque_http_request_duration_seconds",
    "HTTP request latency",
    ("method", "endpoint"),
    registry=registry,
)
HTTP_ERRORS = Counter(
    "e_estoque_http_errors_total",
    "HTTP 5xx errors",
    ("method", "endpoint"),
    registry=registry,
)
DB_POOL_IN_USE = Gauge("e_estoque_db_pool_in_use", "DB connections in use", registry=registry)
CACHE_HITS = Counter("e_estoque_cache_hits_total", "Cache hits", registry=registry)
CACHE_MISSES = Counter("e_estoque_cache_misses_total", "Cache misses", registry=registry)
BUS_PUBLISHED = Counter(
    "e_estoque_bus_published_total", "Events published", ("exchange", "outcome"), registry=registry
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Mede latência/erros por rota (template, sem ids)."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        route = request.scope.get("route")
        endpoint = getattr(route, "path", None) or request.url.path
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            HTTP_ERRORS.labels(method=request.method, endpoint=endpoint).inc()
            HTTP_REQUESTS.labels(method=request.method, endpoint=endpoint, status=500).inc()
            raise
        elapsed = time.perf_counter() - started
        HTTP_LATENCY.labels(method=request.method, endpoint=endpoint).observe(elapsed)
        HTTP_REQUESTS.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()
        return response


async def metrics_endpoint() -> Response:
    """GET /metrics (padrão Prometheus do .NET)."""
    return Response(content=generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


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
