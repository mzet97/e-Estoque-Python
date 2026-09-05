# ADR-001 — Python 3.14

**Status:** aceito. **Contexto:** baseline do prompt (GA estável, sem pre-releases).
**Decisão:** `requires-python = ">=3.14,<3.15"`; interpretador 3.14.x gerenciado pelo uv.
**Consequências:** recursos modernos disponíveis (StrEnum, slots, Self, pattern matching);
3.15+ só após validar dependências críticas.
