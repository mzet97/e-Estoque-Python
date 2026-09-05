"""Cache Redis (redis-py async) — apenas leituras de referência (ADR-011).

Falha do Redis NUNCA derruba a request: degrada para o banco.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis_async

logger = logging.getLogger(__name__)

REFERENCE_TTL_SECONDS = 900  # 15 min


class ReferenceCache:
    """Cache `reference:{entity}:{id}` com fallback silencioso."""

    def __init__(self, host: str, port: int, password: str) -> None:
        self._client: redis_async.Redis = redis_async.Redis(
            host=host,
            port=port,
            password=password or None,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        self.hits = 0
        self.misses = 0

    async def close(self) -> None:
        await self._client.aclose()

    async def get_json(self, key: str) -> Any | None:
        try:
            raw = await self._client.get(key)
        except Exception as exc:  # noqa: BLE001 - degrada para o banco
            logger.warning("cache get falhou (%s): %s", key, exc)
            return None
        if raw is None:
            self.misses += 1
            return None
        self.hits += 1
        result: Any = json.loads(raw)
        return result

    async def set_json(self, key: str, value: Any) -> None:
        try:
            await self._client.set(
                key, json.dumps(value, ensure_ascii=False), ex=REFERENCE_TTL_SECONDS
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache set falhou (%s): %s", key, exc)

    async def evict_reference(self, entity: str, entity_id: str) -> None:
        try:
            await self._client.delete(f"reference:{entity}:{entity_id}")
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache evict falhou (reference:%s:%s): %s", entity, entity_id, exc)
