# ADR-003 — Clean Architecture / Ports & Adapters

**Status:** aceito. Camadas: `domain` (puro) → `application` (use cases + ports `Protocol`) →
`infrastructure` (SQLAlchemy, aio-pika, redis, keycloak http) → `api` (FastAPI). Dependências só
apontam para dentro. Verificado por import-linter no CI. Sem camadas vazias: cada abstração existe
porque há ≥1 implementação e ≥1 motivo real (repository, uow, message bus, jwks).
