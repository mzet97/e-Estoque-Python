# 01 — CURRENT SYSTEM (.NET 8, comportamento real)

## Visão geral

API REST de gestão de estoque/vendas construída em .NET 8 com Clean Architecture + CQRS (MediatR),
PostgreSQL (EF Core/Npgsql), RabbitMQ (publisher only), Keycloak (OIDC), OData v4 e Gridify para
consultas, observabilidade com OpenTelemetry + Prometheus + Grafana/Loki/Tempo.

## Pipeline HTTP (`Program.cs`)

1. Serilog (console + Loki `http://localhost:3100`, enrich `Application=E-estoque`).
2. `SuppressModelStateInvalidFilter = true` (sem 400 automático de model binding).
3. CORS: policy `Development` (allow all) / `Production` (`https://mzet97.dev`, método GET).
4. DbContext + repositórios + message bus (bus desabilitado em env `Testing`).
5. OData route `odata` (Select/Filter/OrderBy/Expand/Count, `MaxTop=1000`).
6. Auth: Keycloak JWT Bearer (`RequireHttpsMetadata=false`, AudienceValidator exige `e-estoque-client`);
   em `Testing`, scheme falso `Test` autentica tudo com roles `Create`+`User`.
7. `ExceptionMiddleware` → mapeia exceções para `{ "error": "<msg>" }`.
8. `UseAuthentication` → `UseAuthorization` → health `/health` → controllers → Swagger.

## Contrato de resposta

- Queries: `BaseResult<T>` → `{ success, message, data }`;
  listas `BaseResultList<T>` → `{ success, message, data[], pagedResult: { currentPage, pageCount, pageSize, rowCount, firstRowOnPage, lastRowOnPage } }` (página 1-based).
- Create/Update (exceto Categories POST): re-executam `GetById` e devolvem 200 com `BaseResult`.
- `POST api/Categories`: **201** `CreatedAtAction` + header `Location`.
- DELETE: 200 com corpo `{}` (MediatR `Unit` serializado).
- JSON: camelCase na saída; entrada case-insensitive.
- Erros: `NotFoundException`→404, `Core.ValidationException`→400, `ForbiddenAccessException`→403,
  `UnauthorizedAccessException`→401, demais→500; corpo sempre `{ "error": "<mensagem>" }`.

## Semântica de persistência

- **Sem Unit of Work**: cada método de repositório chama `SaveChangesAsync` (transação implícita própria).
- `GetByIdAsync`: `AsNoTracking` `FirstOrDefault(Id)`.
- Delete: `RemoveAsync` = **hard delete** (Category, Company, Product, Inventory, Tax);
  `DisableAsync` = **soft delete** (Customer, Sale) — seta `IsDeleted=true, DeletedAt=now`.
- Soft delete **não** é filtrado nas queries, exceto `CategoryRepository.GetAllAsync` (`DeletedAt == null`).
- Timestamps com `DateTime.Now` (hora local do servidor); colunas `timestamp without time zone`
  (switch legado do Npgsql). `Category.Create` etc. geram `Guid.NewGuid()`.
- Todos os FKs `ON DELETE NO ACTION` (`DeleteBehavior.ClientSetNull` global).

## Regras de negócio ( handlers)

- Create inválido → publica `NotificationError(eventName, errors)` na exchange `noticiation-service`
  (routing key `notification-error`) e lança `Core.ValidationException(errors-joinados-por-vírgula)` → 400.
- Referência inexistente (categoria/empresa/cliente/produto) → `NotFoundException` → 404.
  **Exceção:** Tax com categoria inexistente lança `ValidationException` → 400.
- Delete/get de inexistente → `NotFoundException` (mensagens variam: `"Delete Error"`, `"Not found"`, `"Sale not found"`).
- Venda **não** baixa estoque; totais (`TotalPrice`, `TotalTax`) são calculados pelo chamador.
- Login: POST ao endpoint de token do Keycloak (`grant_type=password`); resposta `TokenViewModel`
  (snake_case do Keycloak → camelCase na resposta). Falha (sem `access_token`) → 403.
- Register: system login (`client_credentials`) → POST admin `/admin/realms/{realm}/users` → login imediato.
- Refresh: `grant_type=refresh_token`.

## Consultas

- `Search*Query` (`BaseSearch`): filtros de **igualdade exata** nomeados + `PageIndex`(1)/`PageSize`(10)/`Order`
  (`"Name"`, `"CreatedAt"`, … ascending); sem filtro → sem ordenação. Inclusões por string (`"Products,Taxs"`).
- `Gridify*Query`: `filter` (sintaxe Gridify), `orderBy`, `page`(1), `pageSize`(10); count pós-filtro;
  **sem ordenação padrão** quando `orderBy` ausente; propriedades tipadas extras são decorativas.
- OData: `/odata/{Products|Categories|Companies|Customers|Inventories|Sales|Taxs}` com
  `$select/$filter/$orderby/$expand/$count`, `$top≤1000`, expansão máx. 10, `$metadata`, `({key})`, `/$count`.

## Observabilidade

- `/metrics` Prometheus (exporter OTel), OTLP gRPC `Otlp-Endpoint` (4317 dev), traces ASP.NET/HttpClient/SQL/EF,
  logs → Loki. Health: `GET /health` (EF DbContext check no .NET via `AddDbContextCheck`).

## Autenticação/Autorização

- Toda controller `[Authorize]`; escritas `[Authorize(Roles = "Create")]` (role realm via claim
  `realm_access.roles` transformada pelo `KeycloakClaimsTransformation`).
- `Auth/*` é `[AllowAnonymous]`.
