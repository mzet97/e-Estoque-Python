# ADR-014 — Semântica de concorrência e delete

**Status:** aceito. Delete: Category/Company/Product/Inventory/Tax = **hard delete**; Customer/Sale =
**soft delete** (`disable()` → `is_deleted/deleted_at`) — paridade exata dos handlers .NET. Leitura não
filtra soft-deleted (exceto `CategoryRepository.all()` que filtra `deleted_at is null` — paridade).
Concorrência: a API original **não** baixa estoque nem tem reserva; vendas não disputam inventário.
Locking otimista/`FOR UPDATE` não introduzidos (não há invariante concorrente a proteger — prompt §63:
"não escolher locking por preferência"). Transação: 1 UoW por request de escrita.
