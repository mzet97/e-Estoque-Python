"""Handlers globais de exceção: corpo {"error": msg} e status do contrato .NET."""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from e_estoque.shared.domain.errors import (
    ConflictError,
    ForbiddenError,
    InfrastructureError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

logger = logging.getLogger(__name__)

_STATUS: dict[type[Exception], int] = {
    ValidationError: 400,
    NotFoundError: 404,
    ConflictError: 409,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    InfrastructureError: 500,
}


def install_exception_handlers(app: object) -> None:
    """Registra handlers FastAPI (app.add_exception_handler por tipo)."""

    def make(status: int) -> object:
        def handler(_request: Request, exc: Exception) -> JSONResponse:
            return JSONResponse(
                status_code=status,
                content={"error": str(exc) if str(exc) else exc.__class__.__name__},
            )

        return handler

    add = getattr(app, "add_exception_handler")
    for exc_type, status in _STATUS.items():
        add(exc_type, make(status))

    def unhandled(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(status_code=500, content={"error": str(exc) or "Error"})

    add(Exception, unhandled)
