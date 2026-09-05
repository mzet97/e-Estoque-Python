# 10 — TEST PLAN

## Pirâmide

1. **Unit (`tests/unit`)** — domínio puro: invariantes (mensagens idênticas ao FluentValidation), VOs,
   enums (fallback parse), eventos, handlers de aplicação com fakes de repositório/bus, mapeamento
   entity→viewmodel, envelopes/paginação, parsers Gridify/OData (casos seguros e inválidos).
2. **API (`tests/api`)** — httpx `AsyncClient` + `ASGITransport` sobre o app real com:
   - override da dependência de auth (equivalente ao `TestAuthenticationHandler`: roles `Create`+`User`);
   - banco de teste em memória (aiosqlite) **apenas** para comportamento de aplicação — nunca para
     afirmar compatibilidade PostgreSQL;
   - RabbitMQ substituído por fake publisher (registro de chamadas).
   Cenários: CRUD completo por recurso, envelopes, 201 só em Categories POST, DELETE→200 `{}`,
   códigos 400/401/403/404/422, filtros/ordenação/paginação, gridify endpoints, auth endpoints (com
   Keycloak mockado via `respx`/fake transport), `/health*`, `/metrics`, `/docs`.
3. **Integration (`tests/integration`, Testcontainers)** — PostgreSQL real: schema Alembic, tipos
   (uuid/numeric/timestamp/varchar/`DateOrder varchar`), constraints/FK NO ACTION, transações, soft delete,
   concorrência de escrita; RabbitMQ real: publish das exchanges/routing keys. **Auto-skip sem Docker**
   (o ambiente de execução atual não tem Docker; CI executa).

## Segurança (obrigatórios)

Sem JWT→401; JWT inválido/expirado/audience errada/assinatura errada→401; sem role→403; com role→200.

## Qualidade

`ruff check` + `ruff format --check` + `mypy --strict src` + import-linter + `pytest --cov`
(meta 80% line / 70% branch) + validação Alembic (`upgrade head` em PG do Testcontainers).

## Convenções

- `pytest.ini`/`pyproject`: `asyncio_mode=auto`, markers `integration`, `docker`.
- Sem xfail para esconder bug; sem skips sem justificativa (o único skip permitido é `requires_docker`).
