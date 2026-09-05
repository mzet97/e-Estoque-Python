"""Cliente Keycloak: login/refresh/system (token endpoint) + register (Admin API).

Fluxos idênticos aos handlers .NET (FormUrlEncoded + JSON Admin API), incluindo
a detecção de falha por ausência de access_token e as mensagens de erro.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from e_estoque.shared.application.message_bus import MessageBus
from e_estoque.shared.domain.errors import ForbiddenError
from e_estoque.shared.domain.notifications import ErrorNotification, LoginUserNotification


@dataclass(frozen=True, slots=True)
class TokenResult:
    """TokenViewModel .NET (camelCase na resposta HTTP)."""

    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    token_type: str
    not_before_policy: str
    session_state: str
    scope: str


class KeycloakClient:
    def __init__(
        self,
        base_url: str,
        realm: str,
        client_id: str,
        client_secret: str,
        bus: MessageBus,
    ) -> None:
        self._bus = bus
        self._base = base_url.rstrip("/")
        self._realm = realm
        self._client_id = client_id
        self._client_secret = client_secret

    def _token_url(self) -> str:
        return f"{self._base}/realms/{self._realm}/protocol/openid-connect/token"

    async def _token_request(self, form: dict[str, str]) -> dict[str, Any] | None:
        async with httpx.AsyncClient() as client:
            response = await client.post(self._token_url(), data=form)
        try:
            payload: dict[str, Any] | None = response.json()
        except ValueError:
            payload = None
        return payload

    def _to_result(self, payload: dict[str, Any] | None) -> TokenResult | None:
        if payload is None or not payload.get("access_token"):
            return None
        return TokenResult(
            access_token=str(payload.get("access_token", "")),
            expires_in=int(payload.get("expires_in", 0)),
            refresh_token=str(payload.get("refresh_token", "")),
            refresh_expires_in=int(payload.get("refresh_expires_in", 0)),
            token_type=str(payload.get("token_type", "")),
            not_before_policy=str(payload.get("not-before-policy", "")),
            session_state=str(payload.get("session_state", "")),
            scope=str(payload.get("scope", "")),
        )

    async def login(self, email: str, password: str) -> TokenResult:
        payload = await self._token_request(
            {
                "grant_type": "password",
                "client_id": self._client_id,
                "username": email,
                "password": password,
                "client_secret": self._client_secret,
            }
        )
        token = self._to_result(payload)
        if token is None:
            await self._bus.publish_error_notification(
                ErrorNotification(message="Invalid username or password")
            )
            raise ForbiddenError("Invalid username or password")
        await self._bus.publish_login_notification(LoginUserNotification(username=email))
        return token

    async def refresh(self, refresh_token: str) -> TokenResult:
        payload = await self._token_request(
            {
                "grant_type": "refresh_token",
                "client_id": self._client_id,
                "refresh_token": refresh_token,
                "client_secret": self._client_secret,
            }
        )
        token = self._to_result(payload)
        if token is None:
            raise ForbiddenError("Invalid refresh token")
        return token

    async def system_login(self) -> TokenResult:
        payload = await self._token_request(
            {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }
        )
        token = self._to_result(payload)
        if token is None:
            raise ForbiddenError("Invalid username or password")
        return token

    async def register(
        self, username: str, password: str, email: str, first_name: str, last_name: str
    ) -> TokenResult:
        system_token = await self.system_login()
        body = {
            "username": username,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "emailVerified": True,
            "enabled": True,
            "attributes": {"attribute_key": "client"},
            "credentials": [{"temporary": False, "type": "password", "value": password}],
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._base}/admin/realms/{self._realm}/users",
                json=body,
                headers={"Authorization": f"Bearer {system_token.access_token}"},
            )
        if not response.is_success:
            raise ForbiddenError("Error creating user")
        return await self.login(username, password)
