# TECHNOLOGY-BASELINE

Baseline tecnológica verificada em 2026-09-04. Versões exatas resolvidas ficam travadas em `uv.lock`;
os limites declarados em `pyproject.toml` garantem apenas versões GA estáveis.

| Componente | Baseline | Notas |
| --- | --- | --- |
| Python | 3.14.x (3.14.6) | GA estável; `requires-python = ">=3.14,<3.15"` |
| FastAPI | 0.14x (GA mais recente estável) | Somente camada HTTP |
| Pydantic | 2.1x | Schemas de request/response e settings |
| SQLAlchemy | 2.0.x | `Mapped[T]`/`mapped_column`, `AsyncSession` |
| Alembic | 1.1x | Migrações (substitui EF Migrations) |
| asyncpg | 0.30+ | Driver PostgreSQL async |
| PostgreSQL | 17 | Igual ao `docker-compose.yml` do projeto .NET |
| redis-py | 5.x/6.x | `redis.asyncio` (infra de paridade; ver ADR-011) |
| aio-pika | 9.x | Publisher RabbitMQ (substitui RabbitMQ.Client 6.8.1) |
| Keycloak | 26 (compose usa 24.0.2) | OIDC/JWT; validação local via JWKS |
| OpenTelemetry | 1.x | API/SDK oficiais; OTLP gRPC |
| prometheus-client | 0.2x | Endpoint `/metrics` |
| pytest / pytest-asyncio | 8.x / 0.24+ | Testes |
| httpx | 0.28+ | `AsyncClient` + `ASGITransport` nos testes de API |
| Testcontainers | 4.x | Integração real com PostgreSQL/RabbitMQ (requer Docker) |
| Ruff | latest | lint + format |
| mypy | 1.x | `strict = true` |
| uv | 0.11+ | Gerenciador de projeto (`uv sync --frozen`) |

Regras:

1. Nenhuma dependência pre-release (RC/beta/alpha) é permitida.
2. Python 3.15+ não é suportado até validação explícita de todas as dependências críticas.
3. Versões efetivamente resolvidas devem ser registradas aqui após `uv lock`.
