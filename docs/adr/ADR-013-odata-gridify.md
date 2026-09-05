# ADR-013 — OData/Gridify: `$filter` via biblioteca `odata-query`; resto como adapter próprio

**Status:** aceito (revisado em 2026-09-05 — substitui a versão "sem lib própria").

## Contexto

O §45 do master prompt autorizava biblioteca "madura e mantida" **após avaliação**. A primeira
versão desta ADR rejeitou tudo com uma busca insuficiente; revisão a pedido do owner encontrou
candidatas reais. Critérios: servir (não consumir) OData v4, SQLAlchemy 2 + async, segurança
(sem `eval`, whitelist), Python 3.14, manutenção.

## Avaliação (pesquisa + spike executável contra os models reais)

| Biblioteca | Veredito | Evidência |
| --- | --- | --- |
| `sqlalchemy-odata` | **Descartada — direção errada** | É um *dialeto*/adapter Shillelagh para **consumir** APIs OData via SQL (caso de uso Superset); não serve queries OData |
| `odata-v4-query` (daireto) | **Descartada** | No PyPI é **apenas parser** (sem backend SQLAlchemy publicado); adoção minúscula (4 stars, sem releases no GitHub); exigiria escrever a tradução na mão de qualquer forma |
| `pyodata` / `python-odata` | **Descartadas** | São *clients* para consumir serviços OData |
| **`odata-query` 0.10.0 (gorilla)** | ✅ **Adotada para `$filter`** | MIT; packaged no Fedora; gramática sly madura; **spike aprovado** no projeto: SQLAlchemy 2 `Select` + Python 3.14 + `eq/contains/startswith/or`, uuid/datetime/bool, campo desconhecido → `InvalidFieldException` (erro seguro) |

## Decisão

1. **`$filter` OData → `odata-query`** (`odata-query>=0.10,<1`). O parser da lib substitui o
   grammar-parser manual (que tinha precedência/escapes/parênteses artesanais). Camada de integração
   em `filtering/odata_filter.py`:
   - `WhitelistOrmVisitor` (subclass de `AstToSqlAlchemyOrmVisitor`):
     `visit_Identifier` resolve nomes OData (PascalCase/camelCase) **apenas no FieldMap da entidade**
     — navegações ficam inalcançáveis; campo fora da whitelist → 400.
   - `visit_Compare` coage literais ao `python_type` da coluna (uuid/decimal/datetime/date/int/float)
     — drivers estritos (asyncpg) exigem o tipo certo.
   - `build_odata_filter()` traduz falhas de gramática/valor → `ValidationError` (HTTP 400).
2. **`$orderby`/`$top`/`$skip`/`$count`/`$select`/rotas/`$metadata`** permanecem nossos: a lib **não**
   cobre essas opções (cobre só o filtro); são traduções triviais sem parser.
3. **Gridify** continua com parser próprio (`parse_gridify_filter`): a sintaxe (`^=`, `$=`, `*=`,
   `&`/`|`) é específica do Gridify .NET — nenhuma lib OData a cobre.

## Suportado (subset)

`$filter`: `eq/ne/gt/ge/lt/le`, `contains/startswith/endswith`, `and/or/not`, literais
string/int/float/boolean/datetime/GUID, parênteses e precedência (herdados da gramática da lib) ·
`$orderby` · `$top` (≤1000) · `$skip` · `$count=true` · `/$count` · `Set(key)` (incl. `guid'...'`) ·
`$select` · `/$metadata` (CSDL subset).

## Não suportado (explícito)

`$expand`, funções de data (`year()`, `day()`…), aritmética em `$filter`, `$search`, filtro por
navegação. → **400** (`{"error": ...}`). O frontend `e-estoque-next` não consome nenhuma dessas
opções (o query builder `src/utils/odata.ts` não é invocado por nenhum service).

## Testes

- `tests/unit/test_odata_filter_adapter.py` — 13 testes executando o predicate em sqlite:
  PascalCase/camelCase, funções de string, or, coerções (uuid/datetime/bool/decimal/int),
  campo desconhecido, gramática inválida, valor inválido, navegação bloqueada.
- `tests/api/test_odata_auth.py` — contratos HTTP (`$filter`+`$orderby`+`$top`+`$count`,
  `/$count`, `Set(key)`, `/$metadata`).
