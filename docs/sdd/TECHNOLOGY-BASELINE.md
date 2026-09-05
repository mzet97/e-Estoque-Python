# TECHNOLOGY-BASELINE

Baseline tecnológica verificada em 2026-09-04. Versões **resolvidas e travadas em `uv.lock`**
(estado do primeiro `verify.sh` PASS):

| Componente | Baseline declarada | Resolvida (uv.lock) |
| --- | --- | --- |
| Python | 3.14.x | 3.14.6 |
| FastAPI | 0.141.x | **0.141.1** |
| Pydantic | 2.13.x | **2.13.5** |
| SQLAlchemy | 2.0.x | **2.0.52** |
| Alembic | 1.19.x | **1.19.2** |
| asyncpg | 0.31+ | **0.31.0** |
| aio-pika | 9.8+ | **10.0.1** |
| redis-py | 7.0+ | **8.1.0** |
| PyJWT (+crypto) | 2.12+ | **2.13.0** |
| odata-query | 0.10+ | **0.10.0** (parser `$filter` OData v4 — ADR-013) |
| httpx | 0.28+ | **0.28.1** |
| prometheus-client | 0.24+ | **0.26.0** |
| prometheus-fastapi-instrumentator | 8.x | **8.1.0** (métricas HTTP /metrics) |
| uvicorn | 0.40+ | **0.52.4** |
| pytest | 9.x | **9.1.1** |
| mypy / ruff | strict/latest | travados no lock |
| PostgreSQL | 17 | imagem `postgres:17` |

Regras:

1. Nenhuma dependência pre-release (RC/beta/alpha) é permitida.
2. Python 3.15+ não é suportado até validação explícita de todas as dependências críticas.
3. Versões efetivamente resolvidas devem ser registradas aqui após `uv lock`.
