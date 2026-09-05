# ADR-008 — Keycloak via JWKS (PyJWT)

**Status:** aceito. Resource server: valida assinatura via JWKS do realm (descoberta OIDC, cache de
chaves com refresh), `iss`, `exp`, `nbf`, `aud ∈ {e-estoque-client}`. Roles lidas de
`realm_access.roles` (equivalente ao claims transformation). Fluxos de login/refresh/register/system
reproduzem as chamadas HTTP do .NET ao token endpoint e à Admin API. Sem chamada administrativa por
request. Biblioteca: PyJWT + cryptography.
