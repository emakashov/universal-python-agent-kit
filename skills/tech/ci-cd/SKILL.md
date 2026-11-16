---
name: ci-cd
description: CI/CD pipelines and release automation - GitHub Actions and GitLab CI workflows, fast and reproducible quality gates, caching, test matrices, secrets and permissions, artifact builds, versioning, and deployments. Use only when the project has or needs a CI configuration and the task involves creating, changing, or debugging pipelines, release workflows, or deployment automation.
---

# CI/CD

Tier 3. Activate only if the project has CI configuration (`.github/workflows/`,
`.gitlab-ci.yml`, and so on) or the user asks for one. Use the platform the
project already uses.

## Safety

- Pipeline changes take effect on shared infrastructure. Do not push, trigger
  deployments, create tags or releases, or change repository secrets and
  protection rules without explicit permission for that action.
- Never print secrets in logs; never pass them as command-line arguments; never
  commit them. Do not expose secrets to pipelines triggered by untrusted forks.
- Deployment to production stays behind a manual approval unless the project has
  decided otherwise.

## Principles

- **CI runs the same commands as developers.** Define gates once (Makefile,
  `tox`/`nox`, `just`, scripts) and call them from the pipeline. Logic buried in
  YAML cannot be run locally.
- **Fail fast, cheapest first**: lint and format → types → unit tests →
  integration tests → build → slow checks.
- **Reproducible**: install from the lock file (`uv sync --locked`,
  `pip install --require-hashes`), pin tool and runner image versions.
- **Hermetic**: jobs do not depend on each other's leftovers; pass data through
  artifacts explicitly.
- **Fast**: cache dependency downloads keyed by the lock file hash; run
  independent jobs in parallel; cancel superseded runs.
- A red main branch is fixed or reverted first. Do not disable, skip, or mark a
  failing check as allowed-to-fail to get a merge through.

## Gates

Map `ub-quality-gates` onto pipeline stages. Blocking: tests, linter, formatter
check, type checker, lock-file consistency, migrations check. Informational
unless the project decides otherwise: coverage trend, complexity or CRAP,
duplication, mutation testing (scheduled or on changed critical modules, since
it is slow), dependency audit.

A coverage threshold guards against regression; it is not a quality target.
Do not raise it mechanically or game it.

## GitHub Actions

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
          python-version: ${{ matrix.python-version }}
      - run: uv sync --locked
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy .
      - run: uv run pytest --cov --cov-report=xml
```

- Least-privilege `permissions` at the top; widen per job only where needed.
- Pin third-party actions to a full commit SHA; first-party to a major tag at least.
- Do not use `pull_request_target` with a checkout of untrusted code.
- Never interpolate untrusted event fields (`github.event.*.title`, branch
  names) directly into `run:` scripts; pass them through `env:`.
- Set `timeout-minutes`; use OIDC for cloud and package-registry credentials
  instead of long-lived secrets.
- Match the action and tool versions the repository already uses.

## GitLab CI

- Use `stages`, `rules:` (not `only/except`), `needs:` for a DAG, `cache:` keyed
  on the lock file, `artifacts:` with `expire_in` and test `reports:`.
- `interruptible: true` for superseded pipelines; `timeout:` per job.
- Protected and masked variables for secrets; deploy jobs restricted to
  protected branches or tags with `when: manual` for production.
- Reuse with `extends:`, `!reference`, or `include:` rather than copy-paste.

## Releases

- One source of truth for the version; tag from the main branch after gates pass.
- Build the artifact once and promote the same artifact through environments;
  do not rebuild per environment.
- Generate release notes from the changelog or commit convention the project uses.
- Publishing packages or images uses trusted publishing or scoped tokens, and
  happens only from the release workflow, never from a developer machine by
  an agent.
- Every deployment has a rollback procedure that was actually tried.

## Debugging pipelines

Read the first failing step's full log. Reproduce locally with the same command,
versions, and environment variables. Typical causes: lock file out of date,
cache holding stale state, missing service container, tests depending on order
or time zone, secrets unavailable on fork pull requests, different OS or
architecture. Do not fix flakiness with retries; find the cause.
