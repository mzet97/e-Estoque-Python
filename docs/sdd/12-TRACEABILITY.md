# 12 — TRACEABILITY

Legenda: `tests/unit/...`, `tests/api/...`, `tests/integration/...`. Todo FR tem ≥1 teste.

| Requirement | Domain | Handler | API | Persistence | Unit Test | Integration/API Test |
| --- | --- | --- | --- | --- | --- | --- |
| FR-AUTH-001 | — | identity/application/login.py | api/Auth/login | Keycloak HTTP | test_login_handler | api/test_auth_routes.py |
| FR-AUTH-002 | — | identity/application/refresh.py | api/Auth/refresh_token | Keycloak HTTP | test_refresh_handler | idem |
| FR-AUTH-003 | — | identity/application/system_login.py | (interno) | Keycloak HTTP | test_system_login | idem |
| FR-AUTH-004 | — | identity/application/register.py | api/Auth/register | Keycloak Admin | test_register_handler | idem |
| FR-CAT-001..006 | categories/domain/category.py | categories/application/* | api/categories | categories/infrastructure | test_category_domain.py, test_category_handlers.py | api/test_categories_api.py |
| FR-COMP-001..006 | companies/domain/company.py | companies/application/* | api/companies | companies/infrastructure | test_company_domain.py … | api/test_companies_api.py |
| FR-CUST-001..006 | customers/domain/customer.py | customers/application/* | api/customers | customers/infrastructure | test_customer_domain.py … | api/test_customers_api.py |
| FR-INV-001..006 | inventories/domain/inventory.py | inventories/application/* | api/inventories | inventories/infrastructure | test_inventory_domain.py … | api/test_inventories_api.py |
| FR-PROD-001..006 | products/domain/product.py | products/application/* | api/products | products/infrastructure | test_product_domain.py … | api/test_products_api.py |
| FR-SALE-001..006 | sales/domain/{sale,sale_product}.py | sales/application/* | api/sales | sales/infrastructure | test_sale_domain.py … | api/test_sales_api.py |
| FR-TAX-001..006 | taxes/domain/tax.py | taxes/application/* | api/taxs | taxes/infrastructure | test_tax_domain.py … | api/test_taxs_api.py |
| FR-X-001 | — | — | /health,/health/live,/health/ready | — | — | api/test_health.py |
| FR-X-002 | — | — | /odata/* | filtering/odata.py | unit/test_odata_parser.py | api/test_odata.py |
| FR-X-003 | — | — | /metrics | bootstrap/observability.py | — | api/test_metrics.py |
| NFR-ARCH-001/002 | — | — | — | — | unit/test_architecture.py (import-linter) | CI |
| NFR-SEC-* | — | — | shared/api/security.py | — | unit/test_jwt_validator.py | api/test_security.py |
| NFR-DATA-001 | — | — | — | alembic/0001 | — | integration/test_schema_parity.py |
| NFR-REL-001 | — | — | — | shared/infrastructure/rabbitmq.py | unit/test_rabbit_publisher.py | integration/test_rabbit_publish.py |
