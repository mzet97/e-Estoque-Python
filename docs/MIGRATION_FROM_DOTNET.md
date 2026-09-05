# MIGRATION FROM .NET — guia conceitual (para o dev .NET aprendendo Python)

| .NET | Python (este projeto) | Diferenças / abordagem idiomática |
| --- | --- | --- |
| ASP.NET Core | FastAPI | Routers = controllers; middleware = exception handlers + dependencies |
| Controller | `APIRouter` + funções finas | Sem atributos mágicos; dependências explícitas (`Depends`) |
| MediatR | Handlers explícitos (classes) injetados | Sem bus genérico: `CreateCategoryHandler(repo, bus)` — tipado, testável (ADR-004) |
| FluentValidation | Métodos `validate()` no domínio (mensagens preservadas) + Pydantic na boundary | Domínio é a fonte da verdade das regras |
| EF Core | SQLAlchemy 2.0 async (`Mapped[T]`) | Unit of work = `AsyncSession` context manager |
| EF Migrations | Alembic | `alembic revision --autogenerate` sob revisão humana |
| `IConfiguration` | `pydantic-settings` | Type-safe, `.env` |
| `Guid` | `uuid.UUID` | `uuid4()` para novos |
| `decimal` | `decimal.Decimal` | Nunca `float` para dinheiro |
| `async Task<T>` | `async def -> T` | `await` obrigatório; sem `.Result`/`.Wait()` |
| `IRepository<T>` | `Protocol` por contexto | Structural typing, sem hierarquia ABC |
| DI container | `Depends` + composition root (`create_app`) | Wiring explícito no bootstrap |
| RabbitMQ.Client | aio-pika | `robust_connection`, topic exchange durable |
| Redis (StackExchange) | `redis.asyncio` | Cliente oficial |
| Keycloak.AuthServices | PyJWT + JWKS (httpx) | Validação local das chaves públicas |
| OpenTelemetry .NET | opentelemetry-python | OTLP gRPC idem |
| Serilog | logging stdlib + JSON formatter | structlog opcional não adotado (menos deps) |
| xUnit/Moq | pytest / unittest.mock | fixtures + `AsyncMock` |
| AutoMapper | mapeamento explícito (funções `to_view`) | Explícito > implícito |
| Gridify | `filtering/gridify.py` (parser allow-list → SQLAlchemy) | Sem `eval`; campos mapeados |
| OData (ASP.NET) | `filtering/odata.py` (subset $filter/$orderby/…) | ADR-013 |

## Conceitos C# → Python

```text
record (positional, sealed)  →  @dataclass(frozen=True, slots=True)
IEnumerable<T> / LINQ        →  list[...] + comprehensions / generator
nullable reference (T?)      →  T | None
property (get; private set)  →  atributo + construtor/métodos que mutam (convenção _priv)
interface                    →  typing.Protocol (duck typing estrutural)
DI (IServiceCollection)      →  construtor + FastAPI Depends (composition root)
enum com valores             →  IntEnum / StrEnum
ValueTask/Task               →  coroutine (await)
```

Regra de ouro: **não** escrever Python como C# (sem getters/setters triviais, sem classes gerente
vazias, sem herança profunda; preferir composição, dataclasses e funções puras no domínio).
