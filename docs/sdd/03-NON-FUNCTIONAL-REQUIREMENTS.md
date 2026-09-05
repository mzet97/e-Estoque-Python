# 03 — NON-FUNCTIONAL REQUIREMENTS

| ID | Requisito | Critério de aceitação |
| --- | --- | --- |
| NFR-ARCH-001 | Modular monolith orientado a domínio; Clean Architecture + CQRS + Ports/Adapters | Camadas respeitadas; testes de arquitetura (import-linter) no CI falham em violação |
| NFR-ARCH-002 | Domínio sem dependência de FastAPI/Pydantic/SQLAlchemy/Redis/RabbitMQ/HTTP | Import-linter: `domain` não importa infra/api |
| NFR-SEC-001 | JWT Keycloak validado localmente (assinatura JWKS, `iss`, `exp`, `nbf`, `aud=e-estoque-client`) | Testes de segurança 401/403 |
| NFR-SEC-002 | Role `Create` exigida em escritas; leitura exige autenticação | Testes 403 para role ausente |
| NFR-SEC-003 | Segredos apenas via env/`.env` (nunca commit); `.env.example` documentado | CI grep + revisão |
| NFR-SEC-004 | Sem `eval`/`exec` em parsing de filtros (Gridify/OData) | Revisão + testes de parser |
| NFR-DATA-001 | Schema PostgreSQL compatível com o .NET (tabelas, tipos, FKs NO ACTION, indexes) | `14-DATABASE-PARITY.md` + integração em PG real |
| NFR-DATA-002 | Money/taxas como `Decimal` (nunca float); timestamps UTC em memória, colunas `timestamp` (naive) por paridade | Testes de unidade |
| NFR-DATA-003 | Paginação defensiva: `page>=1`, `pageSize>=1` (sem teto — paridade); valores inválidos → 422 na boundary | Testes |
| NFR-PERF-001 | Stack async ponta a ponta (asyncpg, aio-pika, redis.asyncio); event loop sem bloqueios | Revisão; testes async |
| NFR-OBS-001 | Logs estruturados JSON (timestamp, level, logger, event, request_id, trace_id quando ativo); sem dados sensíveis | Testes de sanitizer |
| NFR-OBS-002 | OpenTelemetry (traces FastAPI/HTTP/SQLAlchemy) exportável via OTLP; desligável por config | Smoke em dev |
| NFR-OBS-003 | Prometheus `/metrics` + health `/health/live` `/health/ready` `/health` | Testes de API |
| NFR-REL-001 | Falha do RabbitMQ não derruba request: publish é best-effort com log (paridade do fire-and-forget .NET) | Testes com broker ausente |
| NFR-REL-002 | Falha do Redis não corrompe regras (cache não é source of truth; não usado por contrato) | Testes |
| NFR-TEST-001 | Cobertura ≥80% linhas / ≥70% branches; fluxos críticos (validação, authz, soft delete, mensageria) 100% comportamentais | `pytest --cov` no verify |
| NFR-TEST-002 | Testes de integração PostgreSQL/RabbitMQ via Testcontainers (auto-skip sem Docker) | CI |
| NFR-OPS-001 | `uv sync --frozen` reproduz ambiente; `scripts/verify.sh` gate único (ruff, format, mypy, testes, cobertura, alembic) | exit 0/≠0 |
| NFR-OPS-002 | Docker multi-stage, usuário não-root, healthcheck; `docker compose up` sobe API+PG+Redis+RabbitMQ+Keycloak+obs | Smoke |
