"""Segurança (401/403/role Create), health e métricas."""

from __future__ import annotations

import jwt  # noqa: F401 (mantido para documentar a origem dos erros convertidos)
from httpx import ASGITransport, AsyncClient

from e_estoque.shared.domain.errors import UnauthorizedError


async def test_health_parity(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.text == "Healthy"


async def test_health_live(client: AsyncClient) -> None:
    assert (await client.get("/health/live")).status_code == 200


async def test_health_ready(client: AsyncClient) -> None:
    assert (await client.get("/health/ready")).status_code == 200


async def test_metrics_exposes_prometheus(client: AsyncClient) -> None:
    await client.get("/health")
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "e_estoque_http_requests_total" in response.text


async def test_auth_disabled_in_testing_allows_reads(client: AsyncClient) -> None:
    # env Testing autentica qualquer request (equivalente ao TestAuthenticationHandler).
    assert (await client.get("/api/Categories")).status_code == 200


async def test_missing_token_rejected_401(app: object) -> None:
    """Com o validador ativo, ausência de token → 401 {"error": "Unauthorized"}."""

    app.state.auth_disabled = False  # type: ignore[attr-defined]

    class FakeValidator:
        def validate(self, token: str) -> object:
            raise UnauthorizedError("Unauthorized")

    app.state.jwt_validator = FakeValidator()  # type: ignore[attr-defined]
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        without = await http.get("/api/Categories")
        assert without.status_code == 401
        assert without.json() == {"error": "Unauthorized"}

        with_token = await http.get(
            "/api/Categories", headers={"Authorization": "Bearer not-a-jwt"}
        )
        assert with_token.status_code == 401


async def test_role_missing_write_forbidden_403(app: object) -> None:
    from e_estoque.shared.api.security import CurrentUser

    app.state.auth_disabled = False  # type: ignore[attr-defined]

    class FakeValidator:
        def validate(self, token: str) -> CurrentUser:
            return CurrentUser(sub="u1", preferred_username="no-role", roles=["Read"])

    app.state.jwt_validator = FakeValidator()  # type: ignore[attr-defined]
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        read = await http.get("/api/Categories", headers={"Authorization": "Bearer x"})
        assert read.status_code == 200  # leitura ok sem role Create

        write = await http.post(
            "/api/Categories",
            json={"name": "Nome", "description": "descricao", "shortDescription": "ok"},
            headers={"Authorization": "Bearer x"},
        )
        assert write.status_code == 403  # escrita exige role Create
        assert write.json() == {"error": "Forbidden"}


async def test_openapi_available_outside_testing(client: AsyncClient) -> None:
    assert (await client.get("/openapi.json")).status_code == 404  # desligado no Testing
