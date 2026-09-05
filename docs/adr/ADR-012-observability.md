# ADR-012 — Observabilidade

**Status:** aceito. `/metrics` Prometheus via `prometheus-client` (http requests, latência, erros,
pool DB, cache, publishes — sem labels de alta cardinalidade). OpenTelemetry: tracing FastAPI/HTTP/
SQLAlchemy com exportador OTLP gRPC configurável (desligado por padrão; endpoint via settings).
Logs JSON estruturados (timestamp, level, logger, event, request_id; trace_id quando OTel ativo),
sem dados sensíveis (sanitizer de Authorization/tokens/senhas). Compose provê Prometheus/Grafana/
Loki/Tempo (arquivos adaptados do projeto .NET).
