# ADR-011 — Redis: wiring sem cache de contrato

**Status:** aceito. O .NET provisiona Redis no compose mas **não o usa** (zero referências no código).
Paridade exige o serviço disponível; contrato exige ausência de cache no caminho das regras. Decisão:
cliente `redis.asyncio` configurável + health check; nenhuma leitura/escrita de negócio passa por
cache. TTL/invalidação só entram com ganho comprovado (prompt §56).
