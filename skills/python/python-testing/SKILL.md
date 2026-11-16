---
name: python-testing
description: Python testing with pytest - behavior-focused tests, fixtures, parametrization, mocking at boundaries, async tests, coverage, and mutation testing. Use when writing or fixing tests, doing TDD, reviewing test quality, raising coverage, or investigating flaky tests in a Python project.
---

# Python Testing

Tier 2. Implements "test behavior, not implementation" from `ub-engineering` and
the TDD cycle from `ub-workflow` for Python.

## What a good test looks like

- Name states behavior: `test_expired_token_is_rejected`, not `test_validate_2`.
- Arrange, act, assert; one behavior per test; the assertion is on something a
  caller can observe.
- Expected values come from the requirement. Never paste the current output of
  the code as the expectation without checking it independently.
- The test must be able to fail: see it red before making it green.
- Tests are independent of each other and of execution order, and deterministic:
  no real clock, network, randomness, or shared global state.

## Implementation coupling to avoid

- Asserting private attributes or `_helpers`.
- `mock.assert_called_once_with(...)` on an internal collaborator when the result
  could be asserted instead.
- Patching the function under test's own internals to steer it.
- Re-implementing the production algorithm in the test to compute the expectation.
- Snapshot tests accepted without reading the snapshot.

## pytest practice

- Use plain `assert`; `pytest.raises(Error, match=...)` for exceptions;
  `pytest.approx` for floats.
- `@pytest.mark.parametrize` with `ids` for input tables, including boundaries:
  empty, one, many, zero, negative, `None`, unicode, limits.
- Fixtures: small, explicit, narrowest scope that works; `yield` for teardown;
  factory fixtures (`make_user(**overrides)`) over large shared objects. Put shared
  fixtures in `conftest.py` at the lowest directory that needs them. Avoid `autouse`
  except for isolation guards.
- Built-ins first: `tmp_path`, `monkeypatch`, `caplog`, `capsys`.
- Register custom marks in the config; run with `--strict-markers`.

## Test doubles

Mock only at boundaries you do not control or that are slow or nondeterministic:
network, clock, randomness, external services, paid APIs.

- Prefer a fake (in-memory repository, fake clock) or a real local instance
  (SQLite or a containerized database, `tmp_path`) over a mock.
- When mocking, use `autospec=True` or `create_autospec`, and patch where the name
  is looked up, not where it is defined.
- HTTP: `respx`, `responses`, or the framework's test client, if the project has them.
- Time: inject a clock or use `freezegun`/`time-machine` if available.
- Do not mock the database for code whose logic lives in queries. Test it against
  a real database of the same engine.

## Levels

Many fast unit tests of pure logic; fewer integration tests through real adapters
(DB, HTTP app via test client); a few end-to-end checks of critical flows. Keep
levels separable by directory or mark so the fast set runs in seconds.

## Async

Use the plugin the project already has (`pytest-asyncio` or `anyio`). Await the
real coroutine; do not test async code by mocking the event loop.

## Coverage and mutation

- `pytest --cov=<pkg> --cov-branch --cov-report=term-missing`. Look at uncovered
  branches of the code you changed, not at the total.
- Do not add assertion-free tests or `# pragma: no cover` to raise the number.
- For critical logic run mutation testing if `mutmut` is installed
  (`mutmut run`, `mutmut results`, `mutmut show <id>`). Each surviving mutant is a
  missing assertion, an equivalent mutant, or dead code. See `ub-quality-gates`.

## Flaky tests

Treat as a bug with a root cause: shared state, ordering, time, concurrency,
network. Reproduce with repetition or random order (`pytest-repeat`'s `--count`,
`pytest-randomly`'s `-p randomly`) if the plugins exist. Do not add retries or
`sleep` to hide it.

## When tests fail

Read the full failure first. Decide whether the code or the test is wrong. Never
loosen an assertion, add `skip`/`xfail`, or delete a test to get green without
saying so and explaining why the test was wrong.
