# ADR-013 — Compatibilidade OData/Gridify via adapters seguros

**Status:** aceito. O frontend Next.js usa CRUD + paginação `PageIndex/PageSize/Order`; OData tem query
builder pronto mas não invocado; gridify existe na API. Estratégia: adapters internos que convertem
`$filter`/`filter` em expressões SQLAlchemy via **parser próprio com allow-list de campos por entidade**
(proibido `eval`). Suporte OData: `eq,ne,gt,ge,lt,le,and,or,contains,startswith,endswith,null`,
`$orderby`, `$top≤1000/$skip`, `$count=true`, `/$count`, `({key})`, `$select` (projeção de resposta),
`$expand` 1 nível. Resposta `{@odata.context, value[], @odata.count}`. Limitações documentadas
(nenhuma consulta ilimitada: teto de linhas herdado de MaxTop/PageSize).
