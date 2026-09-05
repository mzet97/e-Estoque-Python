# 05 — API CONTRACT

JSON: camelCase na saída (aliases Pydantic); entrada aceita alias camelCase (e snake_case).
Envelope: `{ success: bool, message: str, data: T }` / lista `{ ..., data: [T], pagedResult: { currentPage, pageCount, pageSize, rowCount, firstRowOnPage, lastRowOnPage } }`.
Erros: `{ "error": "<msg>" }` (400 validação de domínio · 401 · 403 · 404 · 422 request inválida · 500).
Auth: `Authorization: Bearer <JWT>`; leitura = autenticado; escrita = role `Create`.

## Endpoints REST

| ID | Method | Route | Auth | Request | Response | Status |
| --- | --- | --- | --- | --- | --- | --- |
| API-AUTH-001 | POST | /api/Auth/login | anon | `{email, password}` | TokenViewModel | 200/403 |
| API-AUTH-002 | POST | /api/Auth/refresh_token | anon | `{token}` | TokenViewModel | 200/403 |
| API-AUTH-003 | POST | /api/Auth/register | anon | `{username, password, confirmPassword, email, firstName, lastName}` | TokenViewModel | 200/403 |
| API-CAT-001 | GET | /api/Categories | JWT | query `name, description, shortDescription, id, createdAt, updatedAt, deletedAt, order, pageIndex=1, pageSize=10` | BaseResultList | 200 |
| API-CAT-002 | GET | /api/Categories/gridify | JWT | `filter, orderBy, page=1, pageSize=10` | BaseResultList | 200 |
| API-CAT-003 | GET | /api/Categories/{id} | JWT | — | BaseResult\<CategoryViewModel\> | 200/404 |
| API-CAT-004 | POST | /api/Categories | JWT+Create | `{name, description, shortDescription}` | BaseResult + Location | **201**/400 |
| API-CAT-005 | PUT | /api/Categories/{id} | JWT+Create | `{name, shortDescription, description}` | BaseResult | 200/400/404 |
| API-CAT-006 | DELETE | /api/Categories/{id} | JWT+Create | — | `{}` | 200/404 |
| API-COMP-001..006 | idem Categories em /api/Companies | campos `{name, docId, email, description, phoneNumber, companyAddress{...}}` | | POST→**200** |
| API-CUST-001..006 | idem em /api/Customers | `{..., customerAddress{...}}` | | DELETE = **soft** |
| API-INV-001..006 | idem em /api/Inventories | `{quantity, dateOrder, idProduct}` | | |
| API-PROD-001..006 | idem em /api/Products | `{name, description, shortDescription, price, weight, height, length, image, idCategory, idCompany}` | | |
| API-SALE-001..006 | idem em /api/Sales | `{quantity, totalPrice, totalTax, saleType, paymentType, deliveryDate, saleDate, paymentDate, idCustomer, idsProducts[]}` | | DELETE = **soft**; search: `saleType`/`paymentType` strings ("pix"…) |
| API-TAX-001..006 | idem em /api/Taxs | `{name, description, percentage, idCategory}` | | categoria inexistente → **400** |
| API-ODATA | GET | /odata/{Products,Categories,Companies,Customers,Inventories,Sales,Taxs,SaleProducts} | JWT | `$filter,$orderby,$top,$skip,$count,$select` (subset — `$expand` não suportado, ADR-013) | `{@odata.context, value[], @odata.count?}` | 200/404 |
| API-ODATA-COUNT | GET | /odata/{set}/$count · /odata/{set}({key}) · /odata/$metadata | JWT | | count·item·CSDL | 200/404 |
| API-H-001 | GET | /health | anon | | `Healthy` | 200 |
| API-H-002/003 | GET | /health/live · /health/ready | anon | | live: `{"status":"alive"}`; ready: deps | 200/503 |
| API-M-001 | GET | /metrics | anon | | Prometheus text | 200 |

## ViewModels (camelCase)

- `CategoryViewModel { id, createdAt, updatedAt, deletedAt, name, description, shortDescription }`
- `CompanyViewModel { ..., name, docId, email, description, phoneNumber, companyAddress }`
- `CustomerViewModel { ..., name, docId, email, description, phoneNumber, customerAddress }`
- `InventoryViewModel { ..., quantity, dateOrder, idProduct, product? }`
- `ProductViewModel { ..., name, description, shortDescription, image, price, weight, height, length, idCategory, category?, idCompany, company? }`
- `SaleViewModel { ..., quantity, totalPrice, totalTax, saleType, paymentType, deliveryDate, saleDate, paymentDate, idCustomer, customer?, products[] }` (`saleType`/`paymentType` serializados como número — paridade do enum .NET)
- `TaxViewModel { ..., name, description, percentage, idCategory, category? }`
- `TokenViewModel { accessToken, expiresIn, refreshToken, refreshExpiresIn, tokenType, notBeforePolicy, sessionState, scope }`

## Fonte .NET

Controllers em `e-Estoque-API.API/Controllers/*.cs` + `Controllers/OData/*.cs`; pipeline em `Program.cs`.
