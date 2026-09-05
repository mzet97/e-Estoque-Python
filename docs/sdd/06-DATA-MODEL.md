# 06 — DATA MODEL

Schema final extraído da migration EF `20250327000516_001` + mappings (`EstoqueDbContext`, legacy
timestamp). Todos os FKs `ON DELETE NO ACTION`. Sem unique keys além das PKs. Sem seed.

## Tabelas

### public."Categories"
| Coluna | Tipo PG | Null |
| --- | --- | --- |
| Id | uuid PK | NO |
| Name | varchar(80) | NO |
| Description | varchar(5000) | NO |
| ShortDescription | varchar(500) | NO |
| CreatedAt / UpdatedAt / DeletedAt | timestamp without time zone | NO / YES / YES |
| IsDeleted | boolean | NO |

### public."Companies"
Id PK; Name, DocId, PhoneNumber varchar(80) NO; Email varchar(250) NO; Description varchar(250) NO;
`CompanyAddress_Street/_Number/_Complement/_Neighborhood/_District/_City/_County/_ZipCode/_Latitude/_Longitude`
varchar(80) NO (**`_County` = coluna do campo `country`** — quirk preservado); audit + IsDeleted.

### public."Customers"
Idêntica a Companies com `CustomerAddress_*` e **Email varchar(80)**.

### public."Products"
Id PK; **Name text** (sem varchar); Description varchar(500); ShortDescription varchar(250);
Price, Weight, Height, Length **numeric** (sem precision); Image varchar(5000);
IdCategory uuid FK→Categories(Id); IdCompany uuid FK→Companies(Id); audit.
Indexes: `IX_Products_IdCategory`, `IX_Products_IdCompany`.

### public.inventories (minúsculas!)
Id PK; Quantity integer NO; **DateOrder varchar(80)** (data como string — quirk preservado);
IdProduct uuid FK→Products(Id); audit. Index `IX_inventories_IdProduct`.

### public."Sales"
Id PK; Quantity integer; SaleType integer; PaymentType integer; TotalPrice, TotalTax numeric;
DeliveryDate, SaleDate, PaymentDate timestamp NO; IdCustomer uuid FK→Customers(Id); audit.
Index `IX_Sales_IdCustomer`.

### public."SaleProducts"
Id PK; Quantity integer; IdProduct uuid FK→Products(Id); IdSale uuid FK→Sales(Id); audit.
Indexes: `IX_SaleProducts_IdProduct`, `IX_SaleProducts_IdSale`.

### public."Taxs" (não "Taxes")
Id PK; Name varchar(80); Description varchar(250); Percentage numeric; IdCategory uuid FK→Categories(Id);
audit. Index `IX_Taxs_IdCategory`.

## Mapeamento EF → SQLAlchemy

- `Entity` base → `TimestampMixin` (`created_at/updated_at/deleted_at/is_deleted`).
- Value objects owned → colunas inline com nomes exatos (`company_address_street` mapeado para
  `CompanyAddress_Street` etc., incluindo `county`).
- `DateTime` em memória é UTC-aware; colunas `TIMESTAMP WITHOUT TIME ZONE` recebem naive-UTC
  (conversão na boundary de persistência).
- `SaleType/PaymentType` → `Integer` (não enum PG).
- `Inventory.date_order` → `String(80)` no banco; domínio valida datetime; repo serializa ISO-8601.

## Alembic

`alembic/versions/0001_initial.py` recria exatamente o schema acima (tabelas entre aspas duplas para
preservar camelCase, `inventories` minúsculas). `alembic upgrade head` idempotente. `Base.metadata.create_all()`
proibido em produção. `__alembic_version__` substitui `__EFMigrationsHistory`.

Paridade detalhada: `14-DATABASE-PARITY.md`.
