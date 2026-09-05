# syntax=docker/dockerfile:1
# Multi-stage: deps (uv) → runtime não-root (python:3.14-slim)

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project --no-dev
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

FROM python:3.14-slim AS runtime
RUN groupadd --system eestoque && useradd --system --gid eestoque eestoque
WORKDIR /app
COPY --from=builder --chown=eestoque:eestoque /app/.venv /app/.venv
COPY --from=builder --chown=eestoque:eestoque /app/src /app/src
COPY --chown=eestoque:eestoque alembic /app/alembic
COPY --chown=eestoque:eestoque alembic.ini /app/alembic.ini
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER eestoque
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health/live')" || exit 1
CMD ["uvicorn", "e_estoque.main:app", "--host", "0.0.0.0", "--port", "8000"]
