---
name: ub-quality-gates
description: Proportionate quality gates adapted from Robert C. Martin's ub-mode companion tools (crapper, dryer, mutator) - tests, coverage, lint, types, complexity, CRAP score, duplication, mutation testing, and how to interpret them as indicators rather than proof. Use for every engineering task when choosing which checks to run, interpreting metrics, or deciding whether work is done.
---

# UB Quality Gates

Tier 1, always active, language-independent. The Python tool mapping is at the end.

## 1. Rules

- **Use only what is installed.** Detect a tool before using it (`command -v`,
  the project's dev dependencies, its CI config). Never install a tool or add a
  dependency without the user's agreement; report the missing gate instead.
- **Prefer the project's own commands** (Makefile, `tox`, `nox`, `just`, CI
  scripts, `pyproject.toml` settings) over the generic ones below.
- **Proportionality.** Choose gates by risk and blast radius, not by habit.
- **Metrics are indicators, not proof.** A green metric does not prove quality and
  a red one does not prove a defect. Never reshape code only to improve a number.

## 2. Which gates to run

| Change | Gates |
|--------|-------|
| Docs, comments, formatting | Linter or formatter if configured |
| Ordinary code change | Affected tests, then full tests, linter, type checker |
| New or changed business logic | The above plus coverage of the changed code and complexity or CRAP |
| Critical logic (money, auth, data integrity, concurrency) | The above plus mutation testing of the changed modules |
| Refactoring | Full tests before and after, unchanged; duplication check if that was the goal |
| Integration surface (DB, HTTP API, queues) | Integration tests against the real technology where the project has them |

## 3. Interpreting each gate

**Tests.** Passing tests prove only what they assert. Check that new tests fail
without the change.

**Coverage.** Low coverage of changed code is a finding. High coverage is not
evidence of good tests: lines can be executed without being asserted. Do not write
assertion-free tests to raise the number.

**Complexity and CRAP.** `CRAP = complexity² × (1 − coverage)³ + complexity`.
Target: CRAP < 10 per function. Above the target, first add behavior tests; then
simplify if the function is genuinely tangled. Justified exceptions are allowed
and must be stated: a flat dispatch table or parser `match`, generated code, a
function whose split would scatter one cohesive algorithm. Do not split a function
into fragments just to lower the score.

**Duplication.** A similarity score (for example ≥ 0.8) is a prompt to look, not
an order to merge. Remove duplication when the copies represent the same knowledge
and must change together. Keep it when the similarity is coincidental, when the
copies belong to different bounded contexts, in tests where explicitness helps, or
when the shared abstraction would be harder to read than the copies.

**Mutation testing.** A surviving mutant means a behavior change no test noticed.
For each survivor decide: missing assertion (add a behavior test), equivalent
mutant (ignore, say so), or dead code (delete it). Run it on the changed, critical
modules, not on the whole codebase by default; it is slow.

**Types and lint.** Fix findings in code you touched. Do not silence a finding
with an ignore comment unless it is a false positive, and then explain it inline.

## 4. Reporting

For each gate report: the command, the result, and for anything skipped, why
(not installed, not relevant, too slow for this change). "Not run" is an
acceptable report; an invented result is not.

## 5. Python tool mapping

Use a tool only if present. Prefix with the project's runner (`uv run`, `poetry run`,
`tox -e`, or the active virtualenv).

| Gate | Tool | Typical command |
|------|------|-----------------|
| Tests | pytest | `pytest -q` |
| Coverage | pytest-cov / coverage | `pytest --cov=<pkg> --cov-report=term-missing --cov-report=json` |
| Lint, format | Ruff | `ruff check .` and `ruff format --check .` |
| Types | mypy or Pyright | `mypy <pkg>` or `pyright` (use the one the project configures) |
| Complexity | radon | `radon cc -s -n C <pkg>` |
| CRAP | kit script (needs radon and `coverage.json`) | `python <kit>/tools/crap.py --coverage coverage.json <pkg>` |
| Duplication | pylint `duplicate-code`, or dryer | `pylint --disable=all --enable=duplicate-code <pkg>` |
| Mutation | mutmut (or mutator) | `mutmut run` then `mutmut results` |
| Dependencies | pip-audit | `pip-audit` |
| Security lint | Ruff `S` rules or bandit | `ruff check --select S .` |

`python <kit>/tools/check_tools.py` lists which of these are available in the
current environment. The Uncle Bob companion tools (`crapper`, `dryer`, `mutator`,
`uml-viewer`) are optional: use them if installed and if they support the
project's language; otherwise use the equivalents above.

Technology-specific checks (migrations apply cleanly, API schema is unchanged,
container builds) are described in the Tier 3 skills.
