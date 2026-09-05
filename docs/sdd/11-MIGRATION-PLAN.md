# 11 — MIGRATION PLAN

Vertical slices com loop SDD (SPEC → TEST → IMPLEMENT → VERIFY → REFACTOR → DOCUMENT → COMMIT).
Gate: nenhuma slice avança com lint/mypy/testes/arquitetura quebrados.

| Slice | Conteúdo | Status |
| --- | --- | --- |
| 0 | Discovery (2 repositórios) + docs SDD | ✅ |
| 1 | Bootstrap uv/pyproject, settings, logging, shared domain, DB infra (engine/session/UoW), Alembic 0001 | ✅ |
| 2 | Identity (Keycloak client, JWT/JWKS, roles), segurança API, Company (domínio→API) | ✅ |
| 3 | Category | ✅ |
| 4 | Product | ✅ |
| 5 | Inventory | ✅ |
| 6 | Customer (soft delete) | ✅ |
| 7 | Tax | ✅ |
| 8 | Sales (soft delete, SaleProduct) | ✅ |
| 9 | RabbitMQ publisher (exchanges/routing keys, best-effort) | ✅ |
| 10 | Redis wiring + health | ✅ (ADR-011: wiring sem cache no contrato) |
| 11 | Gridify + OData adapters | ✅ (subset ADR-013) |
| 12 | Observabilidade (OTel, /metrics, /health*) | ✅ |
| 13 | Docker multi-stage + compose + GitHub Actions + verify.sh | ✅ |
| 14 | Parity validation (API/DATABASE parity + frontend smoke) + relatório final | ✅ (ver FINAL-REPORT) |

Resultado dos gates (`scripts/verify.sh`): **PASS** — ruff · format · mypy strict · Alembic offline ·
pytest **82 passed / 2 skipped** (integração Docker) · cobertura **80% linhas / 71% branches**.

## Estratégia de compatibilidade

1. Schema e rotas preservados literalmente (aspas/case/minúsculas incluídos).
2. Envelope, códigos HTTP e mensagens de erro idênticos.
3. Bugs do .NET preservados por padrão (ex.: filtro ShortDescription→Description, ProductUpdated sem
   image, Tax categoria→400, longitude sem validação), exceto onde documentado em
   `MIGRATION-DIFFERENCES.md` como BUG-FIX consciente (não quebram contrato).
4. Frontend `e-estoque-next` é o consumidor de referência para smoke de paridade.
