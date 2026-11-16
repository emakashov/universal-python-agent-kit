---
name: python-packaging
description: Python packaging and dependency management - pyproject.toml, uv, lock files, virtual environments, src layout, entry points, building wheels and sdists, versioning, and publishing. Use when creating or changing pyproject.toml, adding or upgrading dependencies, fixing install or import problems, or building and releasing a Python package.
---

# Python Packaging

Tier 2. Use the project's existing tool (uv, Poetry, PDM, Hatch, pip-tools, plain
pip). Do not migrate between tools unless asked. Examples below use uv; translate
them to the project's tool.

## Rules

- `pyproject.toml` is the single source of project metadata (PEP 621). Do not add
  `setup.py` or `setup.cfg` to a project that does not have them.
- Never edit the lock file by hand; regenerate it with the tool. Commit the lock
  file for applications; follow the project's convention for libraries.
- Adding, removing, or upgrading a dependency changes the project's supply chain:
  do it only when the task needs it and the user agrees, and report it.
- Never `pip install` into the system interpreter. Work in the project environment.
- Publishing is an external, irreversible action: only on explicit request.

## pyproject.toml essentials

```toml
[project]
name = "my-package"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.27"]

[project.scripts]
my-cli = "my_package.cli:main"

[dependency-groups]            # PEP 735; dev tools are not runtime dependencies
dev = ["pytest>=8", "pytest-cov", "ruff", "mypy"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- `requires-python` must match what is actually tested.
- Libraries: lower bounds only, no upper pins without a known incompatibility.
  Applications: loose constraints in `pyproject.toml`, exact versions in the lock.
- Keep tool configuration in `pyproject.toml` (`[tool.ruff]`, `[tool.pytest.ini_options]`,
  `[tool.mypy]`, `[tool.coverage.*]`).

## uv workflow

| Task | Command |
|------|---------|
| Create or sync the environment | `uv sync` |
| Add a runtime / dev dependency | `uv add <pkg>` / `uv add --dev <pkg>` |
| Remove | `uv remove <pkg>` |
| Upgrade one package | `uv lock --upgrade-package <pkg>` |
| Run in the environment | `uv run pytest` |
| Check the lock is current (CI) | `uv lock --check`, `uv sync --locked` |
| Build | `uv build` |
| Publish (explicit request only) | `uv publish` |

## Layout

- Prefer the `src/` layout for libraries: tests then run against the installed
  package, not the working directory.
- Tests live outside the package (`tests/`) and are not shipped unless intended.
- Include `py.typed` in typed libraries.
- Non-code files must be declared as package data and read with
  `importlib.resources`, not with paths relative to `__file__`.

## Building and releasing

1. Tests, lint, and types pass on all supported Python versions.
2. Version updated in one place; changelog updated if the project keeps one.
3. `uv build` (or `python -m build`); inspect the wheel and sdist contents: no
   secrets, tests, or junk; all needed data files present.
4. Install the wheel into a clean environment and run a smoke test of the entry point.
5. Tag and publish only with explicit permission; prefer trusted publishing (OIDC)
   over long-lived tokens. Do not print or store tokens.

## Diagnosing install and import problems

- Confirm the interpreter and environment: `uv run python -c "import sys; print(sys.executable)"`.
- Confirm what is installed and from where: `uv pip list`, `uv pip show <pkg>`,
  `python -c "import pkg; print(pkg.__file__)"`.
- `ModuleNotFoundError` for the project's own package usually means it is not
  installed in the environment (missing build system or `uv sync`), not a need
  for `sys.path` edits. Do not add `sys.path` hacks.
- Resolver conflicts: read which constraints conflict; relax the narrowest one
  that is safe rather than pinning everything.
