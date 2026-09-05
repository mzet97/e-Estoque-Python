#!/usr/bin/env bash
# Gate único de qualidade (equivalente ao `mvn verify` do prompt SDD §132).
# Falha (exit != 0) se QUALQUER etapa falhar.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> 1/6 uv sync (lockfile congelado)"
uv sync --frozen

echo "==> 2/6 Ruff (lint)"
uv run ruff check src tests scripts

echo "==> 3/6 Ruff (format)"
uv run ruff format --check src tests scripts

echo "==> 4/6 mypy --strict"
uv run mypy src

echo "==> 5/6 Alembic (validação offline do SQL da migration inicial)"
uv run alembic upgrade head --sql > /tmp/eestoque_alembic.sql
grep -q 'CREATE TABLE public."Products"' /tmp/eestoque_alembic.sql
grep -q 'CREATE TABLE public."Taxs"' /tmp/eestoque_alembic.sql
grep -q 'CREATE TABLE public.inventories' /tmp/eestoque_alembic.sql
grep -q 'IX_inventories_IdProduct' /tmp/eestoque_alembic.sql

echo "==> 6/6 Testes + cobertura"
uv run pytest tests --cov=e_estoque --cov-branch --cov-report=term-missing

echo ""
echo "VERIFY: PASS"
