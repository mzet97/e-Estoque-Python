# 12 — TRACEABILITY

Arquivos de teste reais deste repositório. Todo FR tem ≥1 teste; a superfície HTTP inteira
(75 rotas) está travada por `tests/api/test_endpoint_matrix.py::test_route_inventory_75_routes_locked`.

| Requirement | Domain | Handlers | API Router | Persistence | Unit Test | API/Integration Test |
| --- | --- | --- | --- | --- | --- | --- |
| FR-AUTH-001..004 | — | identity/application/keycloak_client.py | identity/api/auth_router.py | Keycloak HTTP/Admin | — | api/test_odata_auth.py (login ok/403), api/test_endpoint_matrix.py (register ok/403, refresh ok/403) |
| FR-CAT-001..006 | product/domain/category.py | product/application/category_handlers.py | product/api/category_router.py | product/infrastructure/category_repository.py | unit/test_category_domain.py, unit/test_handlers.py | api/test_crud_parity.py, api/test_endpoint_matrix.py (get/put), api/test_odata_auth.py (odata) |
| FR-COMP-001..006 | company/domain/company.py | company/application/company_handlers.py | company/api/company_router.py | company/infrastructure/company_repository.py | unit/test_party_domains.py, unit/test_handlers.py | api/test_crud_parity.py (roundtrip), api/test_endpoint_matrix.py (search/gridify/404) |
| FR-CUST-001..006 | customer/domain/customer.py | customer/application/customer_handlers.py | customer/api/customer_router.py | customer/infrastructure/customer_repository.py | unit/test_party_domains.py, unit/test_handlers.py (soft delete) | api/test_crud_parity.py (sale flow), api/test_endpoint_matrix.py (roundtrip soft delete) |
| FR-INV-001..006 | inventory/domain/inventory.py | inventory/application/inventory_handlers.py | inventory/api/inventory_router.py | inventory/infrastructure/inventory_repository.py | unit/test_catalog_domains.py, unit/test_handlers.py | api/test_crud_parity.py, api/test_endpoint_matrix.py (get/put/delete/gridify) |
| FR-PROD-001..006 | product/domain/product.py | product/application/product_handlers.py | product/api/product_router.py | product/infrastructure/product_repository.py | unit/test_catalog_domains.py, unit/test_handlers.py | api/test_crud_parity.py, api/test_endpoint_matrix.py (get/put/delete/gridify) |
| FR-SALE-001..006 | sale/domain/sale.py | sale/application/sale_handlers.py | sale/api/sale_router.py | sale/infrastructure/sale_repository.py | unit/test_catalog_domains.py, unit/test_handlers.py (soft delete) | api/test_crud_parity.py (flow), api/test_endpoint_matrix.py (list/put/gridify) |
| FR-TAX-001..006 | tax/domain/tax.py | tax/application/tax_handlers.py | tax/api/tax_router.py | tax/infrastructure/tax_repository.py | unit/test_catalog_domains.py, unit/test_handlers.py | api/test_crud_parity.py (400 categoria), api/test_endpoint_matrix.py (get/put/delete/search/gridify) |
| FR-X-001 | — | — | shared/api/health.py | db | — | api/test_security_health.py (200/503) |
| FR-X-002 | — | — | filtering/odata.py, filtering/sets.py | filtering/odata_filter.py | unit/test_odata_filter_adapter.py, unit/test_wire_filtering_pagination.py (parsers) | api/test_odata_auth.py (sets/filter/count/key/metadata) |
| FR-X-003 | — | — | bootstrap/observability.py | — | — | api/test_security_health.py (métricas expostas) |
| FR-X-004 | — | — | main.py (docs_url) | — | — | api/test_security_health.py (openapi) |
| NFR-ARCH-001/002 | — | — | — | — | unit/test_architecture.py | CI (falha pipeline) |
| NFR-SEC-001..004 | — | — | shared/api/security.py | — | unit/test_architecture.py (sem eval) | api/test_security_health.py (401/403) |
| NFR-DATA-001 | — | — | — | alembic/versions/0001_initial.py | — | integration/test_containers_parity.py (PG real, CI) |
| NFR-REL-001 | — | — | — | shared/infrastructure/messaging/bus.py | unit (FakeBus best-effort) | — |
