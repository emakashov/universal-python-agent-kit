---
name: python-code-review
description: Python code review focused on finding real defects - correctness, error handling, concurrency, security, test quality, and design, with severity-ranked findings and evidence. Use when reviewing a diff, pull request, branch, or file in a Python project, or when self-reviewing changes before reporting them as done.
---

# Python Code Review

Tier 2. A review looks for defects first, design second, style last. Style that a
formatter or linter enforces is not a review finding.

## Procedure

1. Understand the intent: task, PR description, linked issue. Review against the
   intent, not against how you would have written it.
2. Read the whole diff, then the surrounding code and the callers of every changed
   function. Bugs hide in what the diff did not update.
3. Run or read the tests. Check that new tests fail without the change.
4. Verify each suspected defect before reporting it: trace the code path or run
   it. Report only what you can support, and mark uncertain findings as such.

## What to look for

**Correctness**
- Boundaries: empty, `None`, zero, negative, large, duplicate, unicode inputs.
- Off-by-one, wrong operator, inverted condition, mutated argument, shared
  mutable default, late-binding closure.
- All callers and all branches updated; return types consistent on every path.
- Timezones, float money, integer division, encoding.

**Error handling**
- Swallowed or over-broad exceptions; lost cause (`from exc` missing).
- Resources not released on the error path; partial writes without a transaction.
- Error messages that leak secrets or internals.

**Concurrency and async**
- Shared state without a clear owner; check-then-act races; blocking calls inside
  `async def`; missing `await`; tasks without owner or timeout.

**Security** (details in `python-security`)
- Injection via string-built SQL, shell, paths, templates; unsafe deserialization;
  missing authorization check; secrets in code or logs; unvalidated external input.

**Tests**
- Do tests assert behavior or mirror the implementation? Would they catch a
  plausible bug? Are expectations derived independently?
- Missing tests for the error paths and boundaries of the change.
- Tests weakened, skipped, or deleted in the diff.

**Design**
- Subtract before you add: unneeded abstraction, config, dependency, or layer.
- Dependency direction: domain code importing framework or I/O details.
- Duplicated knowledge that must change together.
- Public API or schema changes that break callers; missing migration.

**Operability**
- Logging adequate and free of sensitive data; N+1 queries; unbounded memory,
  loops, or retries; missing timeouts.

## Reporting findings

Order by severity. For each finding give: location (`path:line`), what is wrong,
a concrete failing scenario (input → wrong result), and a suggested fix.

- **Blocker**: wrong behavior, data loss, security hole, broken API.
- **Major**: likely bug, missing test for risky logic, design that will cause defects.
- **Minor**: clarity, naming, small simplification.
- **Question**: intent unclear; ask rather than assume.

State what was reviewed and what was not (for example "did not run integration
tests"). If nothing serious was found, say so plainly; do not pad the review
with nits. Do not fix code during a review unless asked.

## Reviewing agent-written code

Check specifically for: tests that pass because they assert the implementation's
own output, invented APIs or parameters that do not exist in the installed library
version, unrequested abstractions and files, silent scope creep, and claims of
verification without a run.
