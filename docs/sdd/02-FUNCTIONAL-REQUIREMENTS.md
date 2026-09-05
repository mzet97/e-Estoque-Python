# 02 — FUNCTIONAL REQUIREMENTS

Formato: `FR-<CTX>-<NNN>`. Fonte = código .NET + testes. Todos os FRs exigem teste (ver `12-TRACEABILITY.md`).

## Auth (`/api/Auth`, anônimo)

### FR-AUTH-001 — Login
**Input** `{ email, password }`. **Behavior** password grant no Keycloak (`realms/{realm}/protocol/openid-connect/token`,
`client_id`, `client_secret`). **Output** 200 `TokenViewModel` (`accessToken, expiresIn, refreshToken,
refreshExpiresIn, tokenType, notBeforePolicy, sessionState, scope`). **Errors** sem `access_token` → publica
`ErrorNotification("Invalid username or password")` + 403 `{"error":"Invalid username or password"}`;
sucesso publica `LoginUserNotification { username }` (exchange `noticiation-service`, key `login-user-notification`).

### FR-AUTH-002 — Refresh token
**Input** `{ token }` → `grant_type=refresh_token`. **Output** 200 `TokenViewModel`. **Errors** sem token → 403 `"Invalid refresh token"`.

### FR-AUTH-003 — System login
Sem input → `grant_type=client_credentials`. **Errors** → 403 `"Invalid username or password"`.

### FR-AUTH-004 — Register user
**Input** `{ username, password, confirmPassword, email, firstName, lastName }` (`confirmPassword` não é verificado — paridade).
Fluxo: system login → `POST {auth}/admin/realms/{realm}/users` (payload com `attributes.attribute_key="client"`,
`credentials[0] = { temporary:false, type:"password", value }`, `emailVerified:true`, `enabled:true`) → login.
**Errors** admin API falha → 403 `"Error creating user"`.

## Categories (`/api/Categories`)

### FR-CAT-001 — Create (201)
`{ name, description, shortDescription }`; validação: name 3–80, shortDescription 3–500, description 3–5000
(não vazios). Gera `uuid4`, `createdAt=now`, evento `CategoryCreated` → exchange `category-service`.
201 + `Location: /api/Categories/{id}` + `BaseResult<CategoryViewModel>`. Inválido → 400 (join por `,`).

### FR-CAT-002 — Update (200)
`{ id(rota), name, shortDescription, description }`; inexistente → 404 `"Find Error"`; atualiza `updatedAt`, evento `CategoryUpdated`.

### FR-CAT-003 — Delete (hard)
`DELETE /{id}` → inexistente 404 `"Delete Error"`; existente: **hard delete**, 200 `{}`.

### FR-CAT-004 — Get by id (200/404)
404 `"Not found"`; inclui `products` e `taxs` no EF (View populada quando presentes).

### FR-CAT-005 — Search
Query: `name, description, shortDescription, id, createdAt, updatedAt, deletedAt, order, pageIndex, pageSize`
(igualdade exata; **BUG preservado**: `shortDescription` filtra a coluna `Description`). Order aceita
`Id, Name, Description, ShortDescription, CreatedAt, UpdatedAt, DeletedAt` (default `Id`). Includes `Products,Taxs`.

### FR-CAT-006 — Gridify search
`GET /gridify?filter&orderBy&page&pageSize`; campos mapeáveis: `id, name, description, shortDescription,
createdAt, updatedAt, deletedAt, isDeleted`. Count pós-filtro, sem ordenação default.

## Companies (`/api/Companies`)
### FR-COMP-001..006 — CRUD+busca análogos a Category, com campos
`{ name(3–80), docId(3–80), email(3–250), description(3–250), phoneNumber(3–80),
companyAddress: { street, number, complement, neighborhood, district, city, country, zipCode, latitude, longitude } }`
— cada campo de endereço 3–80 não vazio, **`longitude` sem validação** (paridade). POST → **200**.
Eventos → `company-service`. Delete = hard. **Nota**: update .NET publica em `category-service` (bug);
Python publica em `company-service` (BUG-FIX documentado).

## Customers (`/api/Customers`)
### FR-CUST-001..006 — análogos (endereço `customerAddress`); **Delete = soft** (`DisableAsync`);
evento `CustomerCreated/Updated` → `customer-service`.

## Inventories (`/api/Inventories`)
### FR-INV-001 — Create
`{ quantity(>0), dateOrder, idProduct }`; valida estoque **antes** de checar produto; produto inexistente → 404
`"Product not found"`; evento `InventoryCreated` → `inventory-service`.
### FR-INV-002..006 — update (checa estoque+produto), delete hard, get, search
(`quantity, dateOrder, idProduct` + base; includes `Product, Product.Category, Product.Company`),
gridify (`id, idProduct, quantity, createdAt, updatedAt, deletedAt, isDeleted`).
**Paridade de schema**: `date_order` é `varchar(80)` no PostgreSQL — recebido ISO-8601, validado como
datetime, persistido como string, retornado como string (comportamento do contrato; ver `ASSUMPTIONS.md`).

## Products (`/api/Products`)
### FR-PROD-001 — Create
`{ name(3–250), description(3–500), shortDescription(3–250), price>0, weight>0, height>0, length>0,
image(3–5000), idCategory, idCompany }`; categoria inexistente → 404, empresa inexistente → 404;
evento `ProductCreated` (sem `image` no payload — paridade) → `product-service`. POST → 200.
### FR-PROD-002..006 — update (checa produto/categoria/empresa), delete hard, get (inclusões Category+Company+Address),
search (`name, description, shortDescription, price, weight, height, length, idCategory, idCompany` + base; **sem imagem**; sem includes no handler .NET — categoria/empresa nulas na view de search, paridade),
gridify (inclui `image`, `idCategory`, `idCompany`).

## Sales (`/api/Sales`)
### FR-SALE-001 — Create
`{ quantity>0, totalPrice>0, totalTax>0, saleType∈{1,2}, paymentType∈{1,2,3,4}, deliveryDate,
saleDate, paymentDate, idCustomer, idsProducts[] }`; cliente/produto inexistente → 404; cria 1 `SaleProduct`
por produto com a **mesma `quantity` da venda** (paridade); evento `SaleCreated` → `sale-service`. POST → 200.
### FR-SALE-002..006 — update, **delete soft** (404 `"Sale not found"` quando inexistente), get
(includes Customer+SaleProducts+Product+Category+Company), search (`quantity, totalPrice, totalTax,
saleType(string→int), paymentType(string→int), deliveryDate, saleDate, paymentDate, idProduct(any line), idCustomer`),
gridify (`id, idCustomer, saleDate + campos audit`).

## Taxes (`/api/Taxs`)
### FR-TAX-001 — Create
`{ name(3–80), description(3–250), percentage∈[0,100], idCategory }`; categoria inexistente →
**400 `ValidationException("Category not found")`** (não 404 — paridade); evento `TaxCreated` → `tax-service`.
### FR-TAX-002..006 — update (404 `"Tax not found"`; categoria inexistente → 400; erros joinados por `""`),
delete hard (404 `"Delete Error"`), get (include Category), search (`name, description, percentage, idCategory`),
gridify (`id, name, description, percentage, idCategory` + audit).

## Cross-cutting

### FR-X-001 — Health
`GET /health` (paridade) + `GET /health/live` + `GET /health/ready` (verifica PostgreSQL).

### FR-X-002 — OData subset
`GET /odata/{entitySet}` com `$filter` (eq/ne/gt/ge/lt/le/contains/startswith/endswith, and/or),
`$orderby`, `$top`(≤1000)/`$skip`, `$count=true`, `/$count`, `({key})`, `$select`.
**Fora do subset**: `$expand`, funções de data, aritmética, literais `null`/boolean (ADR-013 —
o frontend não consome essas opções). Implementação própria (sem lib — nenhuma candidata madura
para FastAPI/SQLAlchemy async). Resposta `{ "@odata.context", "value": [...] }` (+`"@odata.count"`).

### FR-X-003 — Métricas
`GET /metrics` Prometheus (http requests/latency/erros, pool DB, cache, publishes).

### FR-X-004 — OpenAPI
`/docs`, `/redoc`, `/openapi.json` (JWT bearer security scheme).
