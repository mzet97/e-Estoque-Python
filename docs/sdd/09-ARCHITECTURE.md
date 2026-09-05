# 09 — ARCHITECTURE

Domain-Oriented Modular Monolith (Clean Architecture + DDD + CQRS + Ports & Adapters), async ponta a ponta.

```text
HTTP (FastAPI)
  → Router fino (valida boundary, monta Command/Query)
    → Handler de aplicação (regra de orquestração, autorização contextual, UoW)
      → Domínio puro (entidades/VO/eventos, validações)
        → Repository port (Protocol)
          → SQLAlchemy adapter (AsyncSession) → PostgreSQL
      → MessageBus port → aio-pika adapter → RabbitMQ (publisher)
```

## Árvore de pacotes

```text
src/e_estoque/
├── main.py                     # composition root (create_app)
├── bootstrap/
│   ├── settings.py             # pydantic-settings (db/redis/rabbit/keycloak/obs/cors)
│   ├── logging.py              # JSON structured logging
│   ├── observability.py        # OTel + Prometheus /metrics
│   └── lifespan.py             # engine, redis, rabbit, jwks
├── shared/
│   ├── domain/                 # Entity base, DomainEvent, errors, Result/PagedResult, uow port
│   ├── application/            # message bus port, clock
│   ├── infrastructure/         # db (engine/session), rabbit publisher, redis, repositories base
│   └── api/                    # envelope, error handlers, security (JWT/roles), pagination, health, metrics
├── domains/
│   ├── categories/  {domain, application, infrastructure, api}
│   ├── companies/   {…}
│   ├── customers/   {…}
│   ├── inventories/ {…}
│   ├── products/    {…}
│   ├── sales/       {…}
│   ├── taxes/       {…}
│   └── identity/    {application (keycloak client), api (auth router)}
├── filtering/                  # gridify parser + odata adapter → SQLAlchemy (safe, allow-list)
└── workers/                    # (reservado; sistema original não tem consumers)
```

## Regras estruturais (verificadas por import-linter)

1. `domain` não importa `application|infrastructure|api|fastapi|pydantic|sqlalchemy|redis|aio_pika`.
2. `application` não importa `infrastructure`/`api` (usa ports).
3. `api` importa `application` (nunca repositórios/SQLAlchemy diretamente).
4. Contextos de domínio não importam uns aos outros (exceto `shared`).

## CQRS

Handlers explícitos (classes `Create*Handler`, `GetById*Handler`, …) injetados via `Depends` nos routers.
Sem MediatR-like genérico (ADR-004). Commands/Queries = frozen dataclasses. UoW controla transação
(1 por request de escrita — paridade com 1 `SaveChanges` por operação no .NET).

## Bootstrap/lifespan

`create_app(settings)`: engine + sessionmaker, JWKS provider, redis (lazy), rabbit publisher (lazy),
OTel init, routers, error handlers, health/metrics. `lifespan` abre/fecha recursos.

## Decisões

ADR-001 python3.14 · ADR-002 fastapi · ADR-003 clean-architecture · ADR-004 cqrs-sem-mediatr ·
ADR-005 sqlalchemy2-async · ADR-006 postgresql-schema-parity · ADR-007 async-architecture ·
ADR-008 keycloak-jwks · ADR-009 rabbitmq-publisher · ADR-010 sem-outbox (paridade) ·
ADR-011 redis-infra-parity · ADR-012 observability · ADR-013 odata-gridify-adapter ·
ADR-014 delete-semantics (hard/soft paridade).
