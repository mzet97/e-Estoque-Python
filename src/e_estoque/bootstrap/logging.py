"""Logging estruturado JSON (timestamp, level, logger, event, request_id).

Sem dados sensíveis: mensagens não incluem tokens/Authorization (sanitização
na emissão — NFR-OBS-001).
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

_SENSITIVE = ("authorization", "password", "refresh_token", "access_token", "secret")

_request_id: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(value: str) -> None:
    _request_id.set(value)


def get_request_id() -> str:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    """Formatter JSON para produção; dança leve com stdlib (sem dependências)."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        lowered = message.lower()
        if any(marker in lowered for marker in _SENSITIVE):
            message = "[redacted: possivel dado sensivel]"
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": message,
            "request_id": getattr(record, "request_id", "") or "",
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(environment: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    if environment == "development":
        handler.setFormatter(logging.Formatter("[%(asctime)s %(levelname)s %(name)s] %(message)s"))
    else:
        handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").handlers[:] = [handler]


class RequestIdFilter(logging.Filter):
    """Injeta o request_id do escopo corrente no record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
