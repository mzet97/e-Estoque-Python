"""Router de Auth — contrato .NET: `api/Auth` (anônimo)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from e_estoque.identity.application.keycloak_client import KeycloakClient, TokenResult
from e_estoque.shared.api.views import DecimalNumber  # noqa: F401 (contrato compartilhado)

router = APIRouter(prefix="/api/Auth", tags=["Auth"])


def _client(request: Request) -> KeycloakClient:
    client: KeycloakClient = request.app.state.keycloak_client
    return client


class LoginRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    token: str


class RegisterUserRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    username: str
    password: str
    confirm_password: str  # paridade: o .NET não verifica a confirmação
    email: str
    first_name: str
    last_name: str = ""


def _view(token: TokenResult) -> dict[str, object]:
    """Serialização camelCase do TokenViewModel (campo `not-before-policy` com hífen)."""
    return {
        "accessToken": token.access_token,
        "expiresIn": token.expires_in,
        "refreshToken": token.refresh_token,
        "refreshExpiresIn": token.refresh_expires_in,
        "tokenType": token.token_type,
        "notBeforePolicy": token.not_before_policy,
        "sessionState": token.session_state,
        "scope": token.scope,
    }


@router.post("/login")
async def login(
    payload: LoginRequest, client: Annotated[KeycloakClient, Depends(_client)]
) -> dict[str, object]:
    token = await client.login(payload.email, payload.password)
    return _view(token)


@router.post("/refresh_token")
async def refresh_token(
    payload: RefreshTokenRequest, client: Annotated[KeycloakClient, Depends(_client)]
) -> dict[str, object]:
    token = await client.refresh(payload.token)
    return _view(token)


@router.post("/register")
async def register(
    payload: RegisterUserRequest, client: Annotated[KeycloakClient, Depends(_client)]
) -> dict[str, object]:
    token = await client.register(
        username=payload.username,
        password=payload.password,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return _view(token)
