"""Endpoints OData (subset) e rotas de autenticação."""

from __future__ import annotations

from httpx import AsyncClient

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


async def test_odata_metadata(client: AsyncClient) -> None:
    response = await client.get("/odata/$metadata")
    assert response.status_code == 200
    assert 'EntityType Name="Products"' in response.text
    assert 'EntitySet Name="Taxs"' in response.text


async def test_odata_products_collection_shape(client: AsyncClient) -> None:
    response = await client.get("/odata/Products")
    assert response.status_code == 200
    body = response.json()
    assert "@odata.context" in body
    assert body["value"] == []


async def test_odata_filter_top_count(client: AsyncClient) -> None:
    for index in range(3):
        payload = {**COMPANY, "name": f"Acme {index}", "docId": f"00000000000{index}"}
        assert (await client.post("/api/Companies", json=payload)).status_code == 200

    response = await client.get(
        "/odata/Companies",
        params={
            "$filter": "contains(name,'Acme')",
            "$orderby": "name desc",
            "$top": 2,
            "$count": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["@odata.count"] == 3
    assert len(body["value"]) == 2
    assert body["value"][0]["Name"] == "Acme 2"  # PascalCase + desc


async def test_odata_count_and_key_lookup(client: AsyncClient) -> None:
    created = (await client.post("/api/Companies", json=COMPANY)).json()["data"]
    count = await client.get("/odata/Companies/$count")
    assert count.status_code == 200 and count.text == "1"

    item = await client.get(f"/odata/Companies({created['id']})")
    assert item.status_code == 200
    assert item.json()["Name"] == "Acme Ltda"

    missing = await client.get(f"/odata/Companies({created['id']}000)")
    assert missing.status_code == 404


async def test_odata_select_projection(client: AsyncClient) -> None:
    created = (await client.post("/api/Companies", json=COMPANY)).json()["data"]
    response = await client.get(f"/odata/Companies({created['id']})", params={"$select": "Name"})
    assert response.status_code == 200
    body = response.json()
    assert body["Name"] == "Acme Ltda"


async def test_auth_login_calls_keycloak(
    monkeypatch: object, app: object, client: AsyncClient
) -> None:
    """Login faz proxy ao token endpoint; sucesso devolve TokenViewModel camelCase."""
    from e_estoque.identity.application.keycloak_client import KeycloakClient

    async def fake_token_request(self: object, form: dict[str, str]) -> dict[str, object]:
        assert form["grant_type"] == "password"
        return {
            "access_token": "tok",
            "expires_in": 300,
            "refresh_token": "r",
            "refresh_expires_in": 3600,
            "token_type": "Bearer",
            "not-before-policy": "0",
            "session_state": "s",
            "scope": "openid",
        }

    monkeypatch.setattr(KeycloakClient, "_token_request", fake_token_request)  # type: ignore[attr-defined]
    response = await client.post(
        "/api/Auth/login", json={"email": "user@x.com", "password": "secret"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["accessToken"] == "tok"
    assert body["refreshExpiresIn"] == 3600
    assert body["notBeforePolicy"] == "0"


async def test_auth_login_invalid_credentials_403(
    monkeypatch: object, app: object, client: AsyncClient
) -> None:
    from e_estoque.identity.application.keycloak_client import KeycloakClient

    async def fake_token_request(self: object, form: dict[str, str]) -> None:
        return None

    monkeypatch.setattr(KeycloakClient, "_token_request", fake_token_request)  # type: ignore[attr-defined]
    response = await client.post(
        "/api/Auth/login", json={"email": "user@x.com", "password": "wrong"}
    )
    assert response.status_code == 403
    assert response.json() == {"error": "Invalid username or password"}
