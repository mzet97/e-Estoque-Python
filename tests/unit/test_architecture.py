"""Testes de arquitetura (equivalente ao import-linter, sem dependências extras).

Regras: domínio puro; application sem infra/api; api nunca importa repositories
diretamente; contextos não importam contextos (exceto via shared).
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "e_estoque"

FORBIDDEN = {
    "domain": [
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "redis",
        "aio_pika",
        "httpx",
        "e_estoque.shared.api",
        "e_estoque.shared.infrastructure",
    ],
    "application": [
        "fastapi",
        "e_estoque.shared.api",
        "e_estoque.shared.infrastructure",
    ],
}

CONTEXTS = {"product", "company", "customer", "inventory", "sale", "tax", "identity"}


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return set(modules)


def _python_files(rel: str) -> list[Path]:
    return sorted((SRC / rel).rglob("*.py"))


def test_domain_has_no_framework_imports() -> None:
    for path in _python_files("shared/domain") + [
        p
        for ctx in CONTEXTS
        if (SRC / ctx / "domain").exists()
        for p in _python_files(f"{ctx}/domain")
    ]:
        for module in _imports_of(path):
            for forbidden in FORBIDDEN["domain"]:
                assert not module.startswith(forbidden), f"{path} importa {module}"


def test_application_has_no_infrastructure_or_api_imports() -> None:
    paths: list[Path] = list(_python_files("shared/application"))
    for ctx in CONTEXTS:
        paths.extend(_python_files(f"{ctx}/application"))
    for path in paths:
        for module in _imports_of(path):
            for forbidden in FORBIDDEN["application"]:
                assert not module.startswith(forbidden), f"{path} importa {module}"


def test_routers_do_not_query_the_database_directly() -> None:
    """Composição é permitida na api (repos/session), mas SQL/regras não."""
    for ctx in CONTEXTS:
        for path in _python_files(f"{ctx}/api"):
            for module in _imports_of(path):
                assert not module.startswith("sqlalchemy"), f"{path} importa {module}"


def test_contexts_do_not_import_each_other_outside_api_composition() -> None:
    for ctx in CONTEXTS:
        for path in (SRC / ctx).rglob("*.py"):
            in_api = path.parts[-2] == "api"
            for module in _imports_of(path):
                if module.startswith("e_estoque."):
                    target = module.split(".")[1]
                    allowed = target == ctx or target == "shared" or (in_api and target in CONTEXTS)
                    assert allowed, f"{path} importa contexto alheio: {module}"
