# 07 — SECURITY MODEL

## Identity Provider

Keycloak (realm `e-estoque`, client confidencial `e-estoque-client`). A API Python é **OAuth2 Resource
Server**: valida JWT localmente via JWKS do realm (OIDC discovery `/.well-known/openid-configuration` →
`jwks_uri`), cacheando chaves. Parâmetros (paridade `appsettings.json`):

- Issuer: `KEYCLOAK_AUTH_SERVER_URL` + `/realms/` + `KEYCLOAK_REALM` (dev: `http://localhost:8080/realms/e-estoque`)
- `aud` deve conter `e-estoque-client`
- `RequireHttpsMetadata=false` (dev) — configurável
- Claims de role: `realm_access.roles` (equivalente ao `KeycloakClaimsTransformation`)

## Biblioteca JWT

`PyJWT` + `cryptography` (assinatura RS256/ES256 conforme realm; `exp`/`nbf`/`iss`/`aud` verificados;
nunca `decode` sem verificação).

## Autorização

- Rotas `/api/Auth/*`: anônimas.
- Leitura (GET): qualquer token válido.
- Escrita (POST/PUT/DELETE): role `Create` (string exata do .NET) → 403 caso contrário.
- Dependências FastAPI: `get_current_user`, `require_role("Create")`; política centralizada em
  `shared/api/security.py` (não espalhada nos routers).

## Multi-tenancy

Inexistente no .NET além de `Product.id_company`. Não inventado (decisão em `ASSUMPTIONS.md`).

## Segredos

Nenhum segredo commitado. `.env.example` com placeholders; compose lê `.env`. Settings via
`pydantic-settings` (`SecretStr` para senhas). `.env` no `.gitignore`.

## Headers/CORS

- CORS: `Development` (allow all) / `Production` (`https://mzet97.dev`, GET) — paridade; origins via Settings.
- Sem `allow_origins=["*"]` + `allow_credentials=True` simultâneos.

## Testes de segurança obrigatórios

Sem JWT→401 · JWT inválido→401 · JWT expirado→401 · JWT sem role→403 (escrita) · com role→200 ·
audience errada→401 · assinatura errada→401.
