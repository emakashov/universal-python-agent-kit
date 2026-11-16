---
name: python-development
description: Python conventions for writing and changing code - modern typing, project structure, data modeling with dataclasses and Pydantic v2, boundary validation, error handling, async basics, and idiomatic style. Use when writing new Python code, adding features, designing modules or APIs, or deciding how to model data and errors in a Python project.
---

# Python Development

Tier 2. Apply together with the Tier 1 core skills. The project's own conventions
(Python version, formatter, layout) override the defaults here.

## Before writing

- Read `pyproject.toml`: supported Python versions, dependencies, tool configs.
  Do not use syntax or stdlib features newer than the minimum supported version.
- Match the layout, naming, and import style of neighboring modules.
- Use the standard library and existing dependencies first. A new dependency needs
  the user's agreement.

## Typing

- Annotate all public functions, methods, and module-level attributes.
- Use built-in generics and unions: `list[str]`, `dict[str, int]`, `X | None`.
- Accept abstract types, return concrete ones: parameters `Sequence`, `Mapping`,
  `Iterable` from `collections.abc`; return `list`, `dict`.
- Avoid `Any`. For unknown input use `object` and narrow it. Use `Protocol` for
  structural interfaces, `Literal` and `enum.StrEnum` for closed sets, `TypedDict`
  for dict-shaped external data, `Self` for fluent returns, `NewType` for IDs
  that must not be mixed.
- `# type: ignore[code]` only with a specific code and a reason.

## Modeling data

- Internal values: `@dataclass(frozen=True, slots=True)` by default.
- Data crossing a trust boundary (HTTP, files, env, queues): validate once at the
  boundary, with Pydantic v2 if the project uses it, and pass typed objects inward.
  Do not re-validate in every layer, and do not pass raw `dict`s through the core.
- Pydantic v2 API: `model_validate`, `model_dump`, `field_validator`,
  `model_validator`, `ConfigDict`. Do not use the v1 names (`parse_obj`, `dict()`,
  `@validator`, `class Config`).
- Make illegal states unrepresentable: prefer a union of small types over one type
  with many optional fields.

## Errors

- Raise specific exceptions; define a small project hierarchy for domain errors.
- Catch only what you can handle, at the level that can handle it. No bare
  `except:` and no `except Exception: pass`.
- Preserve the cause: `raise DomainError(...) from exc`.
- Do not use exceptions for expected outcomes of normal flow when a return value
  (`None`, a result type) states it more clearly.
- Use context managers for every resource: files, locks, connections, sessions.

## Functions and modules

- Small functions, one level of abstraction, no boolean flag parameters that
  switch behavior; keyword-only arguments (`*`) for options.
- No mutable default arguments. No work at import time beyond definitions.
- Keep I/O at the edges; keep core logic pure and directly testable.
- Use `pathlib.Path`, f-strings, comprehensions where they stay readable,
  `enumerate`/`zip(strict=True)`, `datetime` with explicit timezone (UTC inside).
- Use `logging` (or the project's logger), never `print`, in library and service code.
- Configuration comes from the environment or config files through one typed
  settings object, not from scattered `os.environ` reads.

## Async

- Do not mix blocking calls into `async` code; use async libraries or
  `asyncio.to_thread`.
- Use `asyncio.TaskGroup` (3.11+) for structured concurrency; never leave a task
  without an owner. Add timeouts to every external await.
- Do not introduce async into a synchronous codebase for one call site.

## Finishing

Run the project's formatter, linter, type checker, and tests per `ub-quality-gates`.
Comment language follows the rule in `ub-engineering`.
