"""Erros de domínio/aplicação com mapeamento de status HTTP idêntico ao contrato .NET."""

from __future__ import annotations


class DomainError(Exception):
    """Base de erros de domínio/aplicação."""


class ValidationError(DomainError):
    """Regra/invariante violada → HTTP 400 {"error": mensagem}."""


class NotFoundError(DomainError):
    """Recurso não encontrado → HTTP 404 {"error": mensagem}."""


class ConflictError(DomainError):
    """Conflito de estado → HTTP 409."""


class UnauthorizedError(DomainError):
    """Não autenticado → HTTP 401."""


class ForbiddenError(DomainError):
    """Proibido → HTTP 403 {"error": mensagem}."""


class InfrastructureError(DomainError):
    """Falha de infraestrutura → HTTP 500."""
