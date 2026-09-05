# ADR-004 — CQRS sem clone do MediatR

**Status:** aceito. Commands/Queries = frozen dataclasses; handlers = classes explícitas
(`CreateCategoryHandler`, `GetByIdCategoryHandler`…). Sem CommandBus genérico nem reflection:
injeção direta nos routers via `Depends`. Pipeline do MediatR (validação/unhandled) é substituído
por: validação de boundary (Pydantic) + validação de domínio + exception handlers globais.
Motivo: tipagem forte, navegação trivial, menos mágica; comporta evolução para bus/behaviors se
necessário.
