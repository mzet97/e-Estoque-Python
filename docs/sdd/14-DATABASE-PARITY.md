# 14 — DATABASE PARITY

| .NET Table | Python Model | Migration | Compatible | Notes |
| --- | --- | --- | --- | --- |
| public."Categories" | `categories` ORM `CategoryModel` | 0001_initial | ✅ | quoted camelCase |
| public."Companies" | `CompanyModel` | 0001 | ✅ | `CompanyAddress_County` = country (quirk) |
| public."Customers" | `CustomerModel` | 0001 | ✅ | Email varchar(80) |
| public."Products" | `ProductModel` | 0001 | ✅ | Name **text**; numerics unbounded |
| public.inventories | `InventoryModel` | 0001 | ✅ | minúsculas; DateOrder varchar(80) |
| public."Sales" | `SaleModel` | 0001 | ✅ | enums inteiros |
| public."SaleProducts" | `SaleProductModel` | 0001 | ✅ | |
| public."Taxs" | `TaxModel` | 0001 | ✅ | não "Taxes" |
| __EFMigrationsHistory | `alembic_version` | — | 🔶 equivalente | mecanismo de migração difere por design |

Verificações (Testcontainers PG): tipos exatos, nullability, FK `ON DELETE NO ACTION` (8 FKs),
7 indexes (`IX_Products_IdCategory`, `IX_Products_IdCompany`, `IX_inventories_IdProduct`,
`IX_Sales_IdCustomer`, `IX_SaleProducts_IdProduct`, `IX_SaleProducts_IdSale`, `IX_Taxs_IdCategory`),
PKs, ausência de unique extras, timestamps sem fuso.
