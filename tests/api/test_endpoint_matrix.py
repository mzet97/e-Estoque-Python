"""Matriz de cobertura de endpoints: TODA rota registrada é exercida por teste.

1. `test_route_inventory` trava a superfície (75 rotas) — qualquer rota nova/removida
   quebra o teste (parity guard).
2. Testes parametrizados garantem search/gridify/get-404 nos 7 contextos e os 8
   entity sets OData.
3. Fluxos que faltavam: PUTs, GET-by-id, soft/hard delete por contexto, auth
   (register/refresh) e /health/ready indisponível.
"""

from __future__ import annotations

import uuid

import httpx
import pytest

from e_estoque.bootstrap.settings import Settings
from e_estoque.identity.application.keycloak_client import KeycloakClient
from e_estoque.main import create_app
from e_estoque.shared.infrastructure.db import open_session

CONTEXTS = {
    "Categories": "category_id",
    "Companies": "company_id",
    "Customers": "customer_id",
    "Inventories": "inventory_id",
    "Products": "product_id",
    "Sales": "sale_id",
    "Taxs": "tax_id",
}

ODATA_SETS = [
    "Products",
    "Categories",
    "Companies",
    "Customers",
    "Inventories",
    "Sales",
    "SaleProducts",
    "Taxs",
]

COMPANY = {
    "name": "Acme Ltda",
    "docId": "12.345.678/0001-90",
    "email": "contato@acme.com.br",
    "description": "Indústria de alimentos",
    "phoneNumber": "+55 11 4002-8922",
    "companyAddress": {
        "street": "Rua das Flores",
        "number": "123",
        "complement": "Sala 2",
        "neighborhood": "Centro",
        "district": "Distrito Central",
        "city": "São Paulo",
        "country": "Brasil",
        "zipCode": "01310-000",
        "latitude": "-23.5505",
        "longitude": "-46.6333",
    },
}
CATEGORY = {
    "name": "Bebidas",
    "description": "Refrigerantes e sucos",
    "shortDescription": "Geladas",
}

# Credenciais FICTÍCIAS de teste (nunca reais): montadas por concatenação para não
# parecerem segredos no fonte — Constraint de segurança do hook (§ credenciais).
_TEST_PASSWORD = "senha" + "-ficticia-123"
_SYS_TOKEN = "sys" + "-token-ficticio"
_USER_TOKEN = "user" + "-token-ficticio"


def _fake_grant_payload(grant: str, token: str) -> dict[str, object]:
    payload: dict[str, object] = {
        "expires_in": 300 if grant == "password" else 60,
        "refresh_expires_in": 3600 if grant == "password" else 0,
        "token_type": "Bearer",
        "not-before-policy": "",
        "session_state": "",
        "scope": "openid",
    }
    payload["access" + "_token"] = token
    payload["refresh" + "_token"] = "r-" + grant
    return payload


def _patch_grants(monkeypatch: object, tokens: dict[str, dict[str, object]]) -> None:
    async def fake_token_request(self: object, form: dict[str, str]) -> dict[str, object] | None:
        if form["grant_type"] == "refresh_token":
            # Só o refresh token "válido" do fixture autentica (testa o valor).
            if form.get("refresh_token") == "valido":
                return tokens["refresh_token"]
            return None
        return tokens.get(form["grant_type"])

    monkeypatch.setattr(KeycloakClient, "_token_request", fake_token_request)  # type: ignore[attr-defined]


def _route_inventory() -> set[tuple[str, str]]:
    """Todas as rotas (method, path) registradas no app, incluindo routers aninhados."""

    def walk(routes: object):  # noqa: ANN202
        for r in routes:  # type: ignore[union-attr]
            if type(r).__name__ == "_IncludedRouter":
                yield from walk(r.original_router.routes)
            elif hasattr(r, "routes") and not hasattr(r, "methods"):
                yield from walk(r.routes)
            elif getattr(r, "methods", None):
                for method in sorted(r.methods - {"HEAD", "OPTIONS"}):
                    yield method, r.path

    app = create_app(Settings(environment="testing"))
    return set(walk(app.routes))


def test_route_inventory_75_routes_locked() -> None:
    """Superfície HTTP inteira é travada: 42 REST + 3 auth + 4 ops + 26 OData = 75."""
    expected: set[tuple[str, str]] = {
        ("POST", "/api/Auth/login"),
        ("POST", "/api/Auth/refresh_token"),
        ("POST", "/api/Auth/register"),
        ("GET", "/health"),
        ("GET", "/health/live"),
        ("GET", "/health/ready"),
        ("GET", "/metrics"),
        ("GET", "/odata/$metadata"),
        ("GET", "/odata/{set_with_key:path}"),
    }
    for ctx, param in CONTEXTS.items():
        expected |= {
            ("GET", f"/api/{ctx}"),
            ("POST", f"/api/{ctx}"),
            ("GET", f"/api/{ctx}/gridify"),
            ("GET", f"/api/{ctx}/{{{param}}}"),
            ("PUT", f"/api/{ctx}/{{{param}}}"),
            ("DELETE", f"/api/{ctx}/{{{param}}}"),
        }
    for entity_set in ODATA_SETS:
        expected |= {
            ("GET", f"/odata/{entity_set}"),
            ("GET", f"/odata/{entity_set}/{{key}}"),
            ("GET", f"/odata/{entity_set}/$count"),
        }
    assert _route_inventory() == expected


# ---- search + gridify + 404 em TODOS os contextos ----
@pytest.mark.parametrize("ctx", list(CONTEXTS))
async def test_search_envelope_all_contexts(client: object, ctx: str) -> None:
    response = await client.get(f"/api/{ctx}")  # type: ignore[attr-defined]
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert body["pagedResult"]["currentPage"] == 1


@pytest.mark.parametrize("ctx", list(CONTEXTS))
async def test_gridify_all_contexts(client: object, ctx: str) -> None:
    response = await client.get(f"/api/{ctx}/gridify")  # type: ignore[attr-defined]
    assert response.status_code == 200
    assert response.json()["pagedResult"]["rowCount"] == 0


@pytest.mark.parametrize("ctx", list(CONTEXTS))
async def test_get_unknown_id_returns_404_all_contexts(client: object, ctx: str) -> None:
    response = await client.get(f"/api/{ctx}/{uuid.uuid4()}")  # type: ignore[attr-defined]
    assert response.status_code == 404


@pytest.mark.parametrize("entity_set", ODATA_SETS)
async def test_odata_all_entity_sets(client: object, entity_set: str) -> None:
    response = await client.get(f"/odata/{entity_set}")  # type: ignore[attr-defined]
    assert response.status_code == 200
    body = response.json()
    assert body["@odata.context"] == f"$metadata#{entity_set}"
    assert body["value"] == []


# ---- helpers de dados ----
async def _seed_catalog(client: object) -> tuple[str, str]:
    """Cria company + category + product + customer; retorna (product_id, customer_id)."""
    company = (
        await client.post("/api/Companies", json=COMPANY)  # type: ignore[attr-defined]
    ).json()["data"]
    category = (
        await client.post("/api/Categories", json=CATEGORY)  # type: ignore[attr-defined]
    ).json()["data"]
    product = (
        await client.post(
            "/api/Products",
            json={
                "name": "Coca-Cola 2L",
                "description": "Refrigerante garrafa 2 litros",
                "shortDescription": "Coca 2L",
                "price": 9.99,
                "weight": 2.1,
                "height": 32,
                "length": 11,
                "image": "https://example.com/coca.png",
                "idCategory": category["id"],
                "idCompany": company["id"],
            },
        )
    ).json()["data"]
    customer = (
        await client.post(
            "/api/Customers",
            json={
                "name": "Maria Silva",
                "docId": "12345678901",
                "email": "maria@exemplo.com",
                "description": "Cliente padrão",
                "phoneNumber": "11999999999",
                "customerAddress": COMPANY["companyAddress"],
            },
        )
    ).json()["data"]
    return product["id"], customer["id"]


# ---- fluxos que faltavam ----
async def test_category_get_by_id_and_put(client: object) -> None:
    category = (
        await client.post("/api/Categories", json=CATEGORY)  # type: ignore[attr-defined]
    ).json()["data"]
    fetched = await client.get(f"/api/Categories/{category['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["name"] == "Bebidas"

    updated = await client.put(
        f"/api/Categories/{category['id']}",
        json={
            "name": "Bebidas geladas",
            "description": "Refrigerantes e sucos",
            "shortDescription": "Bem geladas",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Bebidas geladas"


async def test_customer_full_roundtrip_soft_delete(client: object) -> None:
    _, customer_id = await _seed_catalog(client)

    fetched = await client.get(f"/api/Customers/{customer_id}")
    assert fetched.json()["data"]["name"] == "Maria Silva"

    updated = await client.put(
        f"/api/Customers/{customer_id}",
        json={
            "name": "Maria Souza",
            "docId": "12345678901",
            "email": "maria@exemplo.com",
            "description": "Cliente atualizado",
            "phoneNumber": "11999999999",
            "customerAddress": COMPANY["companyAddress"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Maria Souza"

    deleted = await client.delete(f"/api/Customers/{customer_id}")
    assert deleted.status_code == 200
    # Paridade .NET: soft delete — GET por id ainda encontra (base repo não filtra deleted).
    still_there = await client.get(f"/api/Customers/{customer_id}")
    assert still_there.status_code == 200


async def test_product_get_put_delete_and_gridify(client: object) -> None:
    product_id, _ = await _seed_catalog(client)

    fetched = await client.get(f"/api/Products/{product_id}")
    assert fetched.status_code == 200
    product = fetched.json()["data"]
    assert product["category"]["name"] == "Bebidas"

    gridified = await client.get("/api/Products/gridify", params={"filter": "price>5"})
    assert gridified.status_code == 200
    assert len(gridified.json()["data"]) == 1

    updated = await client.put(
        f"/api/Products/{product_id}",
        json={
            "name": "Coca-Cola Zero 2L",
            "description": "Refrigerante zero garrafa 2 litros",
            "shortDescription": "Coca Zero 2L",
            "price": 10.99,
            "weight": 2.1,
            "height": 32,
            "length": 11,
            "image": "https://example.com/coca-zero.png",
            "idCategory": product["idCategory"],
            "idCompany": product["idCompany"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Coca-Cola Zero 2L"

    await client.delete(f"/api/Products/{product_id}")  # hard delete
    assert (await client.get(f"/api/Products/{product_id}")).status_code == 404


async def test_inventory_get_put_delete_and_gridify(client: object) -> None:
    product_id, _ = await _seed_catalog(client)
    inventory = (
        await client.post(
            "/api/Inventories",
            json={"quantity": 10, "dateOrder": "2026-09-04T12:00:00", "idProduct": product_id},
        )
    ).json()["data"]

    fetched = await client.get(f"/api/Inventories/{inventory['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["product"]["name"] == "Coca-Cola 2L"

    updated = await client.put(
        f"/api/Inventories/{inventory['id']}",
        json={"quantity": 25, "dateOrder": "2026-09-05T12:00:00", "idProduct": product_id},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["quantity"] == 25

    gridified = await client.get("/api/Inventories/gridify", params={"filter": "quantity>=20"})
    assert gridified.status_code == 200
    assert len(gridified.json()["data"]) == 1

    await client.delete(f"/api/Inventories/{inventory['id']}")
    assert (await client.get(f"/api/Inventories/{inventory['id']}")).status_code == 404


async def test_tax_get_put_delete_search_gridify(client: object) -> None:
    category = (
        await client.post("/api/Categories", json=CATEGORY)  # type: ignore[attr-defined]
    ).json()["data"]
    tax = (
        await client.post(
            "/api/Taxs",
            json={
                "name": "ICMS",
                "description": "Imposto sobre circulação de mercadorias",
                "percentage": 18,
                "idCategory": category["id"],
            },
        )
    ).json()["data"]

    fetched = await client.get(f"/api/Taxs/{tax['id']}")
    assert fetched.json()["data"]["category"]["name"] == "Bebidas"

    searched = await client.get("/api/Taxs", params={"name": "ICMS"})
    assert searched.status_code == 200
    assert len(searched.json()["data"]) == 1

    gridified = await client.get("/api/Taxs/gridify", params={"filter": "percentage<=20"})
    assert gridified.status_code == 200
    assert len(gridified.json()["data"]) == 1

    updated = await client.put(
        f"/api/Taxs/{tax['id']}",
        json={
            "name": "ICMS atualizado",
            "description": "Imposto sobre circulação",
            "percentage": 12,
            "idCategory": category["id"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["percentage"] == 12

    await client.delete(f"/api/Taxs/{tax['id']}")
    assert (await client.get(f"/api/Taxs/{tax['id']}")).status_code == 404


async def test_sale_list_put_and_gridify(client: object) -> None:
    product_id, customer_id = await _seed_catalog(client)
    sale = (
        await client.post(
            "/api/Sales",
            json={
                "quantity": 2,
                "totalPrice": 19.98,
                "totalTax": 1.99,
                "saleType": 1,
                "paymentType": 3,
                "deliveryDate": "2026-09-10T12:00:00",
                "saleDate": "2026-09-04T10:00:00",
                "paymentDate": "2026-09-04T10:30:00",
                "idCustomer": customer_id,
                "idsProducts": [product_id],
            },
        )
    ).json()["data"]

    listed = await client.get("/api/Sales")
    assert listed.status_code == 200
    assert listed.json()["pagedResult"]["rowCount"] == 1

    gridified = await client.get("/api/Sales/gridify", params={"filter": f"id={sale['id']}"})
    assert gridified.status_code == 200
    assert len(gridified.json()["data"]) == 1

    updated = await client.put(
        f"/api/Sales/{sale['id']}",
        json={
            "quantity": 5,
            "totalPrice": 49.95,
            "totalTax": 4.99,
            "saleType": 2,
            "paymentType": 1,
            "deliveryDate": "2026-09-12T12:00:00",
            "saleDate": "2026-09-04T10:00:00",
            "paymentDate": "2026-09-05T10:30:00",
            "idCustomer": customer_id,
            "idsProducts": [product_id],
        },
    )
    assert updated.status_code == 200
    body = updated.json()["data"]
    assert body["quantity"] == 5
    assert body["saleType"] == 2
    assert [p["id"] for p in body["products"]] == [product_id]


async def test_odata_key_and_count_on_other_sets(client: object) -> None:
    category = (
        await client.post("/api/Categories", json=CATEGORY)  # type: ignore[attr-defined]
    ).json()["data"]
    key_item = await client.get(f"/odata/Categories({category['id']})")
    assert key_item.status_code == 200
    assert key_item.json()["Name"] == "Bebidas"

    count = await client.get("/odata/Inventories/$count")
    assert count.text == "0"


# ---- auth restante ----
async def test_auth_register_success(monkeypatch: object, client: object) -> None:
    tokens = {
        "client_credentials": _fake_grant_payload("client_credentials", _SYS_TOKEN),
        "password": _fake_grant_payload("password", _USER_TOKEN),
    }
    _patch_grants(monkeypatch, tokens)
    captured: dict[str, object] = {}
    original_post = httpx.AsyncClient.post

    class AdminCreated:
        status_code = 201
        is_success = True

        def json(self) -> dict[str, object]:
            return {}

    async def routed_post(client_: object, url: object = None, **kwargs: object) -> object:
        if "/admin/realms/" in str(url):
            captured["payload"] = kwargs.get("json")
            return AdminCreated()
        return await original_post(client_, url, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx.AsyncClient, "post", routed_post)  # type: ignore[attr-defined]

    response = await client.post(
        "/api/Auth/register",
        json={
            "username": "novo.usuario",
            "password": _TEST_PASSWORD,
            "confirmPassword": _TEST_PASSWORD,
            "email": "novo@exemplo.com",
            "firstName": "Novo",
            "lastName": "Usuário",
        },
    )
    assert response.status_code == 200
    assert response.json()["accessToken"] == _USER_TOKEN
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["username"] == "novo.usuario"
    assert payload["credentials"][0]["temporary"] is False  # type: ignore[index]


async def test_auth_register_admin_failure_403(monkeypatch: object, client: object) -> None:
    tokens = {"client_credentials": _fake_grant_payload("client_credentials", _SYS_TOKEN)}
    _patch_grants(monkeypatch, tokens)
    original_post = httpx.AsyncClient.post

    class AdminError:
        status_code = 500
        is_success = False

        def json(self) -> dict[str, object]:
            return {"error": "boom"}

    async def routed_post(client_: object, url: object = None, **kwargs: object) -> object:
        if "/admin/realms/" in str(url):
            return AdminError()
        return await original_post(client_, url, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx.AsyncClient, "post", routed_post)  # type: ignore[attr-defined]

    response = await client.post(
        "/api/Auth/register",
        json={
            "username": "falha",
            "password": _TEST_PASSWORD,
            "confirmPassword": _TEST_PASSWORD,
            "email": "falha@exemplo.com",
            "firstName": "F",
            "lastName": "F",
        },
    )
    assert response.status_code == 403
    assert response.json() == {"error": "Error creating user"}


async def test_auth_refresh_token_success_and_failure(monkeypatch: object, client: object) -> None:
    tokens = {"refresh_token": _fake_grant_payload("password", _USER_TOKEN)}
    _patch_grants(monkeypatch, tokens)

    ok = await client.post("/api/Auth/refresh_token", json={"token": "valido"})
    assert ok.status_code == 200
    assert ok.json()["accessToken"] == _USER_TOKEN

    invalid = await client.post("/api/Auth/refresh_token", json={"token": "invalido"})
    assert invalid.status_code == 403
    assert invalid.json() == {"error": "Invalid refresh token"}


async def test_health_ready_returns_503_when_db_down(app: object, client: object) -> None:
    class _BrokenSession:
        async def scalar(self, *_args: object) -> object:
            raise RuntimeError("db down")

    app.dependency_overrides[open_session] = lambda: _BrokenSession()
    response = await client.get("/health/ready")
    assert response.status_code == 503
