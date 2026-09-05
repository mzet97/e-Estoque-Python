# ADR-007 — Arquitetura async ponta a ponta

**Status:** aceito. asyncpg + AsyncSession + aio-pika + redis.asyncio + httpx. Nada síncrono/bloqueante
nos request paths. Horário: `datetime.now(timezone.utc)` em memória; persistência converte para naive
(colunas `timestamp`). Sem mistura de sync sessions. Chamo HTTP externo (Keycloak) com httpx.AsyncClient.
