#!/usr/bin/env python3
"""Report which quality tools are available in the current environment.

Run it with the project's interpreter so that tools installed in the project
environment are found, for example ``uv run python <kit>/tools/check_tools.py``.
Nothing is installed or changed. Standard library only.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys

# (gate, tool, executable, importable module, typical command)
TOOLS = [
    ("tests", "pytest", "pytest", "pytest", "pytest -q"),
    ("coverage", "pytest-cov", None, "pytest_cov", "pytest --cov=<pkg> --cov-branch --cov-report=term-missing --cov-report=json"),
    ("coverage", "coverage", "coverage", "coverage", "coverage run -m pytest && coverage json"),
    ("lint/format", "ruff", "ruff", "ruff", "ruff check . && ruff format --check ."),
    ("types", "mypy", "mypy", "mypy", "mypy <pkg>"),
    ("types", "pyright", "pyright", "pyright", "pyright"),
    ("complexity", "radon", "radon", "radon", "radon cc -s -n C <pkg>"),
    ("mutation", "mutmut", "mutmut", "mutmut", "mutmut run && mutmut results"),
    ("duplication", "pylint", "pylint", "pylint", "pylint --disable=all --enable=duplicate-code <pkg>"),
    ("dependencies", "pip-audit", "pip-audit", "pip_audit", "pip-audit"),
    ("security", "bandit", "bandit", "bandit", "bandit -r <pkg>"),
    ("ub companion", "crapper", "crapper", None, "see the tool's README"),
    ("ub companion", "dryer", "dryer", None, "see the tool's README"),
    ("ub companion", "mutator", "mutator", None, "see the tool's README"),
]


def available(executable: str | None, module: str | None) -> bool:
    if executable and shutil.which(executable):
        return True
    return bool(module) and importlib.util.find_spec(module) is not None


def main() -> int:
    print(f"Interpreter: {sys.executable}\n")
    print(f"{'gate':<13} {'tool':<11} {'status':<10} command")
    missing = []
    for gate, tool, executable, module, command in TOOLS:
        found = available(executable, module)
        if not found:
            missing.append(tool)
        print(f"{gate:<13} {tool:<11} {'installed' if found else 'missing':<10} {command if found else '-'}")
    if missing:
        print(f"\nMissing: {', '.join(missing)}.")
        print("Missing tools are skipped, not installed automatically. See the kit README for setup.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
