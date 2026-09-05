# ADR-012 — Observabilidade

**Status:** aceito (revisado 2026-09-05 — métricas HTTP via `prometheus-fastapi-instrumentator`).

## Métricas

- `/metrics` exposto por **`prometheus-fastapi-instrumentator` 8.1** (namespace `e_estoque`):
  `e_estoque_http_requests_total` (counter por rota/método/status) e
  `e_estoque_http_request_duration_seconds` (histograma de latência) — labels por **template de
  rota**, sem ids (sem alta cardinalidade).
- Contadores de domínio no registro default:
  `e_estoque_bus_published_total{exchange,outcome}` (publishes ok/fail, incrementado pelo
  `DirectMessageBus`).
- Métricas de pool/cache: não expostas enquanto não houver uso real de cache/pool tuning
  (nada as incrementa; evitar séries mortas). Reavaliar junto com ADR-011.

## Tracing

OpenTelemetry **opcional** (extra `[otel]`): FastAPI/HTTPX/SQLAlchemy instrumentados, OTLP gRPC
para Tempo, ativado por `EESTOQUE_OTLP_ENDPOINT` (vazio = desligado).

## Logs

JSON estruturado (timestamp, level, logger, event, `request_id` via contextvars) com sanitização
de dados sensíveis na emissão. Loki/Grafana provisionados no compose.

## Health

`GET /health` (paridade .NET, texto "Healthy") · `/health/live` · `/health/ready` (SELECT 1 no
PostgreSQL, 503 quando indisponível).
