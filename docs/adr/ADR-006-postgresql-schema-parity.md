# ADR-006 — PostgreSQL com paridade literal de schema

**Status:** aceito. Tabelas/colunas preservadas com case e quirks (`inventories` minúsculas,
`"Taxs"`, `CompanyAddress_County`, `DateOrder varchar(80)`, `Products.Name text`, numerics sem
precision). FKs `ON DELETE NO ACTION`. Objetivo: a API Python opera sobre a mesma base de dados da
API .NET (migração sem reescrita de dados). Identificadores UUID mantidos.
