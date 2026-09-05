# ADR-013 — Compatibilidade OData/Gridify via adapters seguros

**Status:** aceito (atualizado 2026-09-05).

## Decisão

Sem biblioteca de OData — **adapter próprio** (subset) sobre FastAPI + SQLAlchemy:

- `shared/application/filtering.py` — parser estruturado (`parse_odata_filter`,
  `parse_gridify_filter`) que produz uma AST (`FilterNode`: Condition/And/Or).
- `shared/infrastructure/sql_filtering.py` — tradução AST → expressões SQLAlchemy com
  **whitelist de campos por entidade** (proibido `eval`/`exec` — §46 do master prompt).
- `filtering/odata.py` — rotas `/odata/{Set}` (`Set(key)`, `/$count`, `/$metadata`) e shape de
  resposta do ASP.NET OData (`@odata.context`, `value`, `@odata.count`, propriedades PascalCase).
- `filtering/sets.py` — registro dos 8 entity sets (modelo + whitelist + colunas).

O mesmo AST atende Gridify (`filter`/`orderBy`) e OData (`$filter`/`$orderby`) — um único caminho
testável até o SQL, com valores sempre vinculados (parâmetros, nunca concatenação).

## Alternativas avaliadas e descartadas

- **Nenhuma lib servidor OData madura para FastAPI/SQLAlchemy 2 async existe hoje** (ex.:
  `pyodata` é apenas *client*; portações Flask/Django estão abandonadas). O §45 autorizava lib
  "madura e mantida **após avaliação**" — a avaliação não encontrou candidata elegível.
- Acoplariam o projeto a ORM/sync legado ou exigiriam parser genérico de superfície grande
  (risco de segurança) para recursos que **o consumidor real não usa**.

## Suportado (subset)

`$filter`: `eq, ne, gt, ge, lt, le`, `contains/startswith/endswith`, `and/or` ·
`$orderby` · `$top` (≤1000) · `$skip` · `$count=true` · rota `/$count` · `Set(key)` (incl.
literal `guid'...'`) · `$select` · `/$metadata` (CSDL subset).

## Não suportado (explícito)

`$expand`, funções de data (`year()`, `day()`…), aritmética, `null`/literais booleanos em
`$filter`, `$search`, filtro em propriedades de navegação. Expressões fora do subset → **400**
(`{"error": ...}`). Justificativa: o frontend `e-estoque-next` possui query builder OData
(`src/utils/odata.ts`) mas **nenhum service o invoca** — o consumo real é CRUD +
`PageIndex/PageSize/Order` + gridify. Ampliar = acrescentar caso no parser + campo na whitelist
(`filtering/sets.py`), com teste.
