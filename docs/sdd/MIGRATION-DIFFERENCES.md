# MIGRATION-DIFFERENCES

Diferenças conscientes entre a API .NET e a API Python. Classificação: `BUG-FIX`, `SECURITY-FIX`,
`FRAMEWORK-DIFFERENCE`, `INTENTIONAL-DESIGN`, `BREAKING-CHANGE`.

| # | Item | Classe | Detalhe |
| --- | --- | --- | --- |
| 1 | Eventos de Company Update publicados em `category-service` (.NET) → `company-service` (Python) | BUG-FIX | Exchange correta; sem consumidores no ecossistema |
| 2 | `page<=0`/`pageSize<=0`: 500 (.NET) → 422 (validação de boundary FastAPI) | BUG-FIX | NFR-DATA-003; 422 é o padrão de validação do FastAPI (ver #11) |
| 3 | `RowCount` dos searches de Product/Inventory/Sale/Tax contado antes do filtro (.NET, derivados) → contado após filtro (Python) | BUG-FIX | Alinha ao comportamento do repositório base .NET e do Gridify path; frontend pagina com rowCount |
| 4 | Include inválido `"SaleProduct"` em `SaleRepository` (.NET) | FRAMEWORK-DIFFERENCE | Join correto por relacionamento (`sale_products`) |
| 5 | `Sale.Customer` não-virtual / lazy loading | FRAMEWORK-DIFFERENCE | Sem lazy loading; aggregates carregados com selectinload/joinedload explícitos |
| 6 | Timestamps: `DateTime.Now` local (.NET) → UTC naive em coluna naive | INTENTIONAL-DESIGN | Prompt §21; coluna preservada |
| 7 | Publish RabbitMQ: síncrono e falha propaga (.NET) → best-effort async pós-commit com log | INTENTIONAL-DESIGN | NFR-REL-001; wire format idêntico |
| 8 | `EnsureCreated`/SQLite nos testes .NET | FRAMEWORK-DIFFERENCE | Testes API em aiosqlite (comportamento) + Testcontainers PG (paridade real) |
| 9 | `Inventory.DateOrder varchar(80)` provavelmente quebrado em PG real no .NET | INTENTIONAL-DESIGN | Mantido varchar; ISO-8601 validado (ASSUMPTIONS A-01) |
| 10 | Bugs preservados voluntariamente (paridade): filtro `shortDescription`→`Description`; `ProductCreated/Updated` sem image; Tax categoria inexistente→400; `totalTax=0` inválido; `longitude` sem validação; enum parse fallback (PIX/UNITARY); messages `"Delete Error"`/`"Not found"`; soft delete sem filtro global | INTENTIONAL-DESIGN | Contrato/precedência §2 |
| 11 | Requests malformados (binding): .NET 400 → FastAPI 422 | FRAMEWORK-DIFFERENCE | Inclui paginação inválida (ver #2); corpo de validação difere |
| 15 | Paginação interna (`paged_search_bounds`) também defensiva com 400 para uso programático | INTENTIONAL-DESIGN | API expõe 422 via FastAPI antes de chegar ao handler |
| 12 | Auth: falha de login → 403 como no .NET | — | Idêntico |
| 13 | Swagger: Swashbuckle → OpenAPI nativo FastAPI (`/docs`) | FRAMEWORK-DIFFERENCE | Mesma informação, UI diferente |
| 14 | `/health` .NET checa DbContext; Python `/health` simples + `/health/ready` com check de DB | INTENTIONAL-DESIGN | Prompt §75 |

Nenhum endpoint foi removido. Nenhuma breaking change de contrato (ver #2, #3 — melhorias sem consumidor dependente).
