# 13 — API PARITY MATRIX

Status: ✅ implementado · 🔶 diferença documentada · ⬜ pendente. Atualizar ao fim de cada slice.

| ID | .NET | Python | Auth | Compatible | Test |
| --- | --- | --- | --- | --- | --- |
| API-AUTH-001 | POST /api/Auth/login | idem | anon | ✅ | api/test_auth |
| API-AUTH-002 | POST /api/Auth/refresh_token | idem | anon | ✅ | api/test_auth |
| API-AUTH-003 | POST /api/Auth/register | idem | anon | ✅ | api/test_auth |
| API-CAT-001/002/003 | GET /api/Categories[/gridify]/{id} | idem | JWT | ✅ | api/test_categories |
| API-CAT-004 | POST /api/Categories → 201+Location | idem | Create | ✅ | api/test_categories |
| API-CAT-005/006 | PUT/DELETE /api/Categories/{id} → 200 | idem | Create | ✅ | api/test_categories |
| API-COMP-001..006 | /api/Companies CRUD+gridify | idem | JWT/Create | ✅ (exchange fix 🔶) | api/test_companies |
| API-CUST-001..006 | /api/Customers (delete soft) | idem | JWT/Create | ✅ | api/test_customers |
| API-INV-001..006 | /api/Inventories | idem | JWT/Create | ✅ | api/test_inventories |
| API-PROD-001..006 | /api/Products | idem | JWT/Create | ✅ | api/test_products |
| API-SALE-001..006 | /api/Sales (delete soft) | idem | JWT/Create | ✅ | api/test_sales |
| API-TAX-001..006 | /api/Taxs | idem | JWT/Create | ✅ | api/test_taxs |
| API-ODATA-001 | /odata/{8 entity sets} $filter/$orderby/$top/$skip/$count/$select/$expand, MaxTop 1000 | subset equivalente (ADR-013) | JWT | 🔶 subset | api/test_odata |
| API-ODATA-002 | /odata/{set}/$count, ({key}), /$metadata | idem (metadata CSDL subset) | JWT | 🔶 | api/test_odata |
| API-H-001 | GET /health | idem | anon | ✅ | api/test_health |
| API-H-002/003 | (novos) /health/live /health/ready | idem | anon | 🔶 adição | api/test_health |
| API-M-001 | GET /metrics (OTel Prometheus) | idem (prometheus-client) | anon | ✅ | api/test_metrics |
| API-S-001 | /swagger, /swagger/v1/swagger.json | /docs, /redoc, /openapi.json | config | 🔶 UI difere | api/test_openapi |

Endpoints .NET inexistentes no Python: nenhum. Endpoints Python extras: `/health/live`, `/health/ready`.
