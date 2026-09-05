# 00 — SOURCE INVENTORY

Fontes analisadas em 2026-09-04:

- **Primária:** `mzet97/e-Estoque-API` — clone local `D:\TI\git\e-Estoque\e-Estoque-API` (solução .NET 8).
- **Secundária:** `mzet97/e-Estoque` — clone local `D:\TI\git\e-Estoque\e-Estoque` (MVC legado C#) e
  `D:\TI\git\e-Estoque\e-estoque-next` (frontend Next.js consumidor real da API).

## Solução .NET (`e-Estoque-API/e-Estoque-API`)

| Projeto .NET | Conteúdo | Destino Python |
| --- | --- | --- |
| `e-Estoque-API.Core` (csproj `e-Estoque-API.Domain.csproj`) | Entidades, `Entity`/`AggregateRoot`, value objects `CompanyAddress`/`CustomerAddress`, domain events, enums `SaleType`/`PaymentType`, interfaces `IRepository<T>`, validações FluentValidation, exceções `NotFoundException`/`ValidationException`, modelos `BaseResult`/`PagedResult` | `src/e_estoque/shared/domain` + `domains/<ctx>/domain` |
| `e-Estoque-API.Application` | CQRS MediatR: Commands/Queries/Handlers por feature (Auth, Categories, Companies, Customers, Inventories, Products, Sales, Taxs), Behaviours (validação/unhandled), ViewModels, GridifyExtensions | `domains/<ctx>/application` |
| `e-Estoque-API.Infrastructure` | `EstoqueDbContext` (Npgsql), mappings EF, migration `20250327000516_001`, repositórios concretos, RabbitMQ producer (`RabbitMqClient`, `ProducerConnection`), `ODataModel` | `shared/infrastructure` + adapters |
| `e-Estoque-API.API` | Controllers REST + OData, `Program.cs`, Keycloak auth (`Keycloak.AuthServices.Authentication`), CORS, Swagger, Serilog+Loki, OpenTelemetry/Prometheus, `ExceptionMiddleware`, `TestAuthenticationHandler` | `src/e_estoque/api` |
| `e-Estoque-API.UnitTest` | xUnit + Moq + FluentAssertions: regras de negócio por feature | `tests/unit` (pytest) |
| `e-Estoque-API.IntegrationTest` | `WebApplicationFactory` + SQLite temp + `TestAuthenticationHandler` + mocks (MessageBus, Auth handlers) | `tests/api` (httpx ASGI) e `tests/integration` (Testcontainers) |
| `load-tests/` | k6 (smoke/load/stress/spike/endurance) | fora do escopo do port; documentado |

## Infraestrutura do compose (.NET)

`postgres:17`, `redis:7.2`, `rabbitmq:3.13-management`, `keycloak:24.0.2` (realm import `my-realm.json`),
`nginx` LB (3 réplicas da API), `prometheus`, `grafana`, `loki`, `tempo`, `jaeger`, `mimir`, `pgadmin`.
Redis **não é usado por código .NET** (grep: zero usos) — mantido como serviço de paridade.

## Componentes-chave mapeados

- Controllers REST: `Auth`, `Categories`, `Companies`, `Customers`, `Inventories`, `Products`, `Sales`, `Taxs` (+ `MainController`).
- Controllers OData: 7 (Categories, Companies, Customers, Inventories, Products, Sales, Taxs).
- Comandos: 3 por recurso (Create/Update/Delete) + 4 de Auth (Login, Refresh, Register, SystemLogin).
- Consultas: 3 por recurso (GetById, Search "BaseSearch", Gridify).
- Repositórios: `Repository<T>` base + 8 derivados.
- Mensageria: `IMessageBusClient.Publish(message, routingKey, exchange)` — **somente publisher** (sem consumers/workers/outbox no .NET).
- Migração EF única: `20250327000516_001` (schema final documentado em `06-DATA-MODEL.md`).
- Realm Keycloak: `e-estoque`, client confidencial `e-estoque-client`, roles `admin, user, Create, Read, Update, Delete`.
