# 10 — TEST PLAN

Estado real da suíte: **141 passed · 2 skipped · cobertura 92% linhas / ~77% branches**.

## Pirâmide

1. **Unit (`tests/unit`, 68 testes)** — domínio puro: invariantes com mensagens idênticas ao
   FluentValidation, VOs, enums (fallback parse), eventos, handlers de aplicação com fakes de
   repositório/bus, wire format do broker, parsers Gridify + adapter OData (`odata-query`,
   executados em sqlite), paginação (`PagedResult`), testes de arquitetura (AST: domínio sem
   frameworks, application sem infra/api, contextos isolados).
2. **API (`tests/api`, 73 testes)** — httpx `AsyncClient` + `ASGITransport` sobre o app real com:
   - override da dependência de auth (equivalente ao `TestAuthenticationHandler`: roles `Create`+`User`);
   - banco de teste em memória (aiosqlite) **apenas** para comportamento de aplicação — nunca para
     afirmar compatibilidade PostgreSQL (essa fica nos Testcontainers);
   - RabbitMQ substituído por `FakeBus` (registro de chamadas); Keycloak mockado por
     `_token_request` (login/refresh/register).
   Cenários: CRUD completo por recurso (search/gridify/get/put/delete), envelopes, 201 só em
   Categories POST, DELETE→200 `{}`, 400/401/403/404/422, soft vs hard delete por contexto,
   gridify e OData (8 entity sets, `$filter/$orderby/$top/$count/$select`, `Set(key)`,
   `/$metadata`), `/health*` (200 e 503), `/metrics`, `openapi` desligado em Testing.
3. **Integration (`tests/integration`, 2 testes, Testcontainers)** — PostgreSQL 17 real: migration
   Alembic aplicada, tabelas/FKs/indexes de paridade; RabbitMQ real: connect + publish. **Auto-skip
   sem Docker** (`EESTOQUE_SKIP_DOCKER`); o CI executa com service containers.

## Travas estruturais

- **Route inventory** (`test_endpoint_matrix.py::test_route_inventory_75_routes_locked`) — o
  conjunto exato de 75 rotas (42 REST + 3 auth + 4 ops + 26 OData) deve bater; rota nova ou
  removida sem atualizar o teste quebra o CI.
- **Arquitetura** (`test_architecture.py`) — importa regras das camadas via AST.

## Qualidade

- Cobertura mínima: **80% linhas** no CI (`--cov-fail-under=80`); atual: 92% / ~77% branches.
- **pip-audit** no job `quality` (vulnerabilidades de dependências; falha o pipeline).
- `./scripts/verify.sh` = gate local completo (sync frozen + ruff + format + mypy strict +
  alembic offline + pytest/cobertura).
