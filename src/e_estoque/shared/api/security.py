"""Segurança cross-cutting: validação JWT via JWKS do Keycloak + roles de realm.

Equivalências .NET: KeycloakClaimsTransformation (realm_access.roles → roles),
AudienceValidator (aud deve conter o client) e TestAuthenticationHandler (env
Testing autentica tudo com role Create). Erros usam exceções de domínio →
corpo {"error": ...} como no ExceptionMiddleware.
"""

from __future__ import annotations

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from e_estoque.bootstrap.settings import Settings
from e_estoque.shared.domain.errors import ForbiddenError, UnauthorizedError

_bearer = HTTPBearer(auto_error=False)

TEST_USER = "test-user-id"
TEST_ROLES = ("Create", "User")


class CurrentUser(BaseModel):
    sub: str
    preferred_username: str = ""
    roles: list[str] = []

    @property
    def can_create(self) -> bool:
        """Role Create do realm (equivalente ao [Authorize(Roles=\"Create\")] .NET)."""
        return "Create" in self.roles


class KeycloakValidator:
    """Valida assinatura/iss/aud localmente com as chaves públicas (JWKS)."""

    def __init__(self, settings: Settings) -> None:
        issuer = settings.keycloak_issuer.rstrip("/")
        self._issuer = issuer
        self._audience = settings.keycloak_client_id
        self._jwks_client = jwt.PyJWKClient(f"{issuer}/protocol/openid-connect/certs")
        self._algorithms = ["RS256"]

    def validate(self, token: str) -> CurrentUser:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=self._algorithms,
                issuer=self._issuer,
                audience=self._audience,
                options={"require": ["exp", "iss"]},
            )
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Unauthorized") from exc
        realm_access = claims.get("realm_access") or {}
        roles = list(realm_access.get("roles", []))
        return CurrentUser(
            sub=str(claims.get("sub", "")),
            preferred_username=str(claims.get("preferred_username", "")),
            roles=roles,
        )


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    """Dependency: exige Bearer válido (401 caso contrário)."""
    if getattr(request.app.state, "auth_disabled", False):
        # Equivalente ao TestAuthenticationHandler (env Testing).
        return CurrentUser(sub=TEST_USER, preferred_username="testuser", roles=list(TEST_ROLES))
    if credentials is None:
        raise UnauthorizedError("Unauthorized")
    validator: KeycloakValidator = request.app.state.jwt_validator
    return validator.validate(credentials.credentials)


def require_create(
    user: CurrentUser = Depends(current_user),
) -> CurrentUser:
    """Dependency: exige role Create nas escritas (403 caso contrário)."""
    if not user.can_create:
        raise ForbiddenError("Forbidden")
    return user
