# ASSUMPTIONS — decisões inferidas (ambiguidade → opção conservadora)

| # | Ambiguidade | Decisão | Justificativa |
| --- | --- | --- | --- |
| A-01 | `Inventory.DateOrder` é `DateTime` no C#, mas `varchar(80)` no PostgreSQL (incompatível em PG real; testes .NET rodam em SQLite) | Coluna permanece `varchar(80)`; API aceita/retorna string ISO-8601; domínio valida datetime | Paridade de schema + contrato (frontend trata `dateOrder` como string ISO) |
| A-02 | Timestamps .NET usam `DateTime.Now` (local) em colunas `timestamp` naive | Python usa UTC-aware em memória e persiste naive-UTC | Prompt §21 (UTC); coluna/tipo preservados; valores diferem apenas no offset |
| A-03 | Paginação sem teto de `pageSize` no .NET | Sem teto (paridade); `page<1`/`pageSize<1` → 400 (BUG-FIX: .NET retornava 500) | Prompt §47; nenhum cliente depende de 500 |
| A-04 | `UpdateCompanyCommandHandler` publica eventos em `category-service` | Publica em `company-service` | BUG-FIX óbvio; nenhum consumidor existe para validar o contrário |
| A-05 | `SearchCategoryQuery` filtra `shortDescription` contra coluna `Description` | Preservado (paridade) | Regra obtida do código; mudar quebraria clientes |
| A-06 | DELETE retorna 200 `{}` (controllers) vs 204 (testes de integração .NET) | 200 `{}` (controllers vencem — precedência §2) | Ordem de precedência do prompt |
| A-07 | POST retorna 201 apenas em Categories; 200 nos demais (vs 201 esperado em testes) | Paridade (200; 201 só Categories) | Precedência §2 |
| A-08 | RabbitMQ publisher síncrono fire-and-forget no .NET | Publish best-effort async pós-commit; falha logada, request não falha | NFR-REL-001; wire format idêntico |
| A-09 | Outbox ausente no .NET | Não implementado (ADR-010) | Não há consumers; adicionar mudaria observável sem demanda |
| A-10 | Redis provisionado mas não usado pelo .NET | Wiring + health apenas; sem cache no caminho do contrato | Prompt §56 (cache só com ganho comprovado) |
| A-11 | Multi-tenancy além de `Product.id_company` não existe | Não inventado | §2 precedência; §54 "quando aplicável" |
| A-12 | `audience` validada contra `e-estoque-client` | Idem no Python (config) | Program.cs AudienceValidator |
| A-13 | `refresh-token` (frontend) vs `refresh_token` (API) | Somente `/api/Auth/refresh_token` (rota real); divergência do frontend registrada | Contrato vence |
| A-14 | Rotas chamadas pelo frontend que não existem (`/Users`, `/Roles`, `/inventories/low-stock`, `/products/sku/{sku}`) | Não criadas | §2: código executável da API vence |
| A-15 | `Sale.Customer` não-virtual, `SaleRepository.Include("SaleProduct")` inválido | N/A em Python (join explícito correto: `sale_products`) | Diferença de framework; comportamento equivalente (sem lazy loading) |
| A-16 | Repos derivados .NET contam rows antes do filtro (RowCount errado em search paginado de Product/Inventory/Sale/Tax) | Python conta **após** filtro (comportamento do `Repository<T>` base e do Gridify path) | BUG-FIX; frontend usa `rowCount` para paginação — valor correto é o pós-filtro (base repo) |
| A-17 | `decimal` PG sem precision (Products/Taxs/Sales) | `Numeric(38, 10)`? **Não** — `Numeric()` sem argumentos (unbounded, igual PG `numeric`) | Paridade exata de schema |
