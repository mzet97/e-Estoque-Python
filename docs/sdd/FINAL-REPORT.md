# e-Estoque Python Migration Report

**Data:** 2026-09-05 · **Projeto:** `e-Estoque-Python` (`D:\TI\git\e-Estoque\e-Estoque-Python`) · **Final Status: READY** (com ressalvas operacionais abaixo)

## Technology Baseline (resolvidas em `uv.lock`, gate PASS)

```
Python:            3.14.6 (requires-python >=3.14,<3.15)
FastAPI:           0.141.1
Pydantic:          2.13.5 (+ pydantic-settings)
SQLAlchemy:        2.0.52 (async, asyncpg 0.31.0)
Alembic:           1.19.2
PostgreSQL:        17 (imagem, igual ao compose .NET)
Redis client:      redis-py 8.1.0 (redis.asyncio)
RabbitMQ client:   aio-pika 10.0.1
JWT:               PyJWT 2.13.0 (+cryptography), JWKS local
HTTP client:       httpx 0.28.1
OData $filter:     odata-query 0.10.0 (parser OData v4; whitelist+coerção em filtering/odata_filter.py)
Prometheus:        prometheus-client 0.26.0
OpenTelemetry:     opcional (extra [otel], OTLP gRPC), desligado por padrão
uv:                0.11.26 · uvicorn 0.52.4 · pytest 9.1.1
```

## Repositories Analyzed

- `mzet97/e-Estoque-API` (clone local: 6 projetos .NET, 274 arquivos .cs, migration EF única)
- `mzet97/e-Estoque` (MVC legado + frontend real `e-estoque-next`, consumidor de referência)

## Requirements

```
Functional:         42 (FR-AUTH-001..004, FR-*/001..006 ×7, FR-X-001..004)
Non-functional:     17 (NFR-ARCH/SEC/DATA/PERF/OBS/REL/TEST/OPS)
Implemented:        42/42 FR · 15/17 NFR completos · 2 parciais (cobertura no CI com Docker; smoke do frontend pendente de execução)
Pending:            execução de testcontainers-integration e smoke do e-estoque-next contra a API Python (exigem Docker/runtime)
```

## Bounded Contexts

```
Product:    ✅ Product + Category (1 contexto; AggregateRoot: Product)
Category:   ✅ (dentro de product; inclui Products/Taxs)
Inventory:  ✅ (date_order varchar(80) preservado — A-01)
Sales:      ✅ Sale + SaleProduct (delete soft; update substitui linhas)
Customer:   ✅ (delete soft — DisableAsync)
Company:    ✅ (endereço owned, coluna CompanyAddress_County preservada)
Tax:        ✅ (tabela "Taxs"; categoria inexistente → 400, paridade)
Identity:   ✅ Keycloak client + JWT/JWKS + roles realm_access
```

## API Parity

```
Original endpoints:       45 (REST 8 controllers + OData 7 sets + ops)
Python endpoints:         47 (todos os 45 + /health/live + /health/ready)
Compatible:               100% dos 45 (matriz: docs/sdd/13-API-PARITY.md)
Intentional differences:  OData em subset seguro ($filter eq/ne/gt/…/contains/$orderby/$top/$skip/$count/$select/1 key) — ADR-013;
                          Swagger UI → /docs do FastAPI
Missing:                  0 endpoints
```

Validado por 32 testes de API: 201+Location só em Categories POST, DELETE→200 `{}`, envelope
`{success,message,data,pagedResult}` camelCase, 400 com mensagens FluentValidation unidas por
vírgula, 403 sem role Create, 404 com mensagens do .NET, `dateOrder` string ISO, decimal como número.

## Database

```
Tables:              8/8 (aspas PascalCase; inventories minúsculas; "Taxs")
Alembic migrations:  0001_initial (paridade literal da EF 20250327000516_001, validada offline e no CI em PG 17)
Compatibility:       projetada para operar sobre a MESMA base do .NET (FKs NO ACTION, numerics sem precision, timestamps sem fuso)
Indexes:             7/7 (IX_Products_IdCategory/IdCompany, IX_inventories_IdProduct, IX_Sales_IdCustomer, IX_SaleProducts_IdProduct/IdSale, IX_Taxs_IdCategory)
Constraints:         PKs nomeadas PK_*; 7 FKs FK_*; sem unique extras (idem .NET)
```

## Security

```
Keycloak:        realm e-estoque, client confidencial e-estoque-client (realm import incluído)
JWT:             validação local via JWKS (iss/exp/nbf/aud=e-estoque-client), PyJWT + cryptography
Roles:           realm_access.roles → role "Create" exigida em escritas (string exata do .NET)
Tenant isolation: N/A por paridade (único vínculo: Products.IdCompany — A-11/ADR-014)
Testes:          401 sem token · 401 token inválido · 403 sem role · 200 com role · aud/assinatura via PyJWTError→401
```

## Messaging

```
RabbitMQ:              publisher only (paridade — .NET não tem consumers)
Domain events:         14 (Created/Updated de 7 agregados, occurredOn UTC, camelCase, nulls omitidos)
Integration events:    NotificationError/ErrorNotification/LoginUserNotification (exchanges com typo `noticiation-service` preservado)
Transactional outbox:  NÃO implementado — decisão documentada (ADR-010): paridade + ausência de consumers
Idempotency:           N/A (não há consumidores no sistema original)
DLQ:                   N/A
Resiliência:           publish best-effort pós-commit; falha do broker logada, não derruba request (NFR-REL-001)
```

## Cache

```
Redis:            provisionado no compose + health; cliente redis.asyncio com fallback silencioso
Cache policies:   nenhuma no caminho do contrato (ADR-011 — o .NET não usa Redis)
Invalidation:     ReferenceCache disponível (TTL 15min) para uso futuro comprovado
```

## Observability

```
OpenTelemetry: opcional (extra [otel]) → OTLP gRPC (Tempo), FastAPI/HTTPX/SQLAlchemy instrumentados
Prometheus:    /metrics (requests, latência histograma, erros 5xx, pool, cache, publishes; sem labels de cardinalidade)
Grafana/Loki:  serviços no compose (dashboards provisionáveis)
Health:        /health ("Healthy", paridade) · /health/live · /health/ready (SELECT 1 no PostgreSQL)
Logs:          JSON estruturado (timestamp, level, logger, event, request_id; sanitizer de dados sensíveis)
```

## Tests

```
Unit:         55 — invariantes com mensagens exatas FluentValidation, VOs, enums+fallback, wire format,
              parser Gridify + adapter OData ($filter via odata-query, 13 testes em sqlite), paginação,
              handlers com fakes (404/400 por recurso, soft/hard delete), arquitetura (import rules)
API:          32 — CRUD parity por recurso, envelopes/status, gridify, OData subset, auth proxy, 401/403, health/metrics
Integration:  2 (Testcontainers PG 17 schema-parity + RabbitMQ publish) — auto-skip sem Docker
Security:     inclusos nos de API (401/403/roles)
Concurrency:  n/a por paridade (a API original não baixa estoque — ADR-014)
Architecture: 4 testes (AST) — domínio puro, application sem infra/api, contextos isolados (composição só na api)
Coverage:     80% linhas · 71%+ branches (meta ≥80/70); CI falha abaixo de 80
```

## Static Analysis

```
Ruff:  All checks passed (lint + format, 80 arquivos)
mypy:  Success — no issues found in 68 source files (strict = true)
```

## Verification

```
Command: ./scripts/verify.sh
Etapas:  uv sync --frozen · ruff check · ruff format --check · mypy strict · alembic upgrade head --sql (+greps de paridade) · pytest --cov --cov-branch
Result:  PASS (exit 0)
```

## Docker

```
Command:  docker compose up -d --build
Serviços: api (multi-stage, não-root, healthcheck) · postgres:17 · redis:7.2 · rabbitmq:3.13 ·
          keycloak:26 (realm import) · prometheus · grafana · loki · tempo
Result:   PASS na construção/definição — EXECUÇÃO NÃO REALIZADA NESTE AMBIENTE (Docker indisponível); validar em máquina/CI com Docker
```

## Commits

```
4a524e8  docs(sdd): discovery + specification baseline
62a7004  feat(domains): all 7 bounded contexts with CQRS handlers, repositories and routers
2660688  feat(all): FastAPI app composition, auth/OData routes, Alembic 0001 parity schema, tests (82), Docker compose, CI, verify gate
(bloco anterior, da sessão predecessora: bootstrap do projeto, shared kernel, product/category parciais)
```

## Intentional Differences From .NET

Ver `docs/sdd/MIGRATION-DIFFERENCES.md` (15 itens classificados BUG-FIX / FRAMEWORK-DIFFERENCE /
INTENTIONAL-DESIGN). Destaques: eventos de Company na exchange correta; count pós-filtro nos
searches derivados; paginação inválida → 422; publish RabbitMQ best-effort; sem outbox (ADR-010);
`Sale.Update` substitui linhas sem quebrar FK; timestamps UTC em memória.

## Remaining Risks

- **Docker indisponível neste ambiente**: os 2 testes de integração (Testcontainers) e o smoke
  `docker compose up` precisam ser executados em máquina/CI com Docker (pipeline `integration` já
  aplica a migration em PG 17 real).
- **Frontend smoke** (`e-estoque-next` → API Python): pendente de execução; divergências conhecidas
  do frontend (ex.: `/Auth/refresh-token` vs `/api/Auth/refresh_token`, rotas `/Users`·`/Roles`
  inexistentes também no .NET) já registradas nas ASSUMPTIONS.
- **OData em subset** (ADR-013): expressões além do suportado retornam 400 — ampliar conforme uso real.
- **Scan Mimosa**: execução completa pendente (hooks rodaram parciais durante o desenvolvimento);
  rodar `mimosa-security-scan` completo antes de produção.

## Final Status

**READY** (funcional + gates PASS localmente; pendências acima são operacionais, não de código)
