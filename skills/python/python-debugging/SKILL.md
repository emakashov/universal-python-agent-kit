---
name: python-debugging
description: Systematic root-cause debugging for Python - reproducing failures, reading tracebacks, forming and testing hypotheses, bisecting, and diagnosing concurrency, async, import, and environment problems. Use when a Python test fails, an exception or wrong result appears, behavior differs between environments, or a previous fix did not hold.
---

# Python Debugging

Tier 2. Implements "root cause over symptom" and "attack the premise" from
`ub-engineering`.

## Procedure

1. **Reproduce.** Get a minimal, repeatable reproduction: one test, one command,
   one input. If it cannot be reproduced, gather evidence (logs, versions, inputs)
   before touching code.
2. **Read the evidence.** Read the whole traceback, bottom frame first, including
   chained exceptions ("The above exception was the direct cause..."). Note the
   exact error type, message, and the first frame in project code.
3. **State a hypothesis** that explains all observations, and predict something
   new that would be true if it holds.
4. **Test the prediction** with the cheapest experiment: an assertion, a log line,
   a debugger breakpoint, a smaller input. Change one thing at a time.
5. **Fix the cause** where it originates, with a regression test written first that
   fails for the right reason.
6. **Verify** the reproduction now passes, the full test suite passes, and remove
   all temporary instrumentation.

## Attack the premise

After two fixes that did not hold, stop. List what you are assuming: which code
actually runs, which version is installed, what the data really looks like, who
else mutates the state, whether the test tests what you think. Verify the
weakest assumption directly:

- Is this the file being imported? `python -c "import pkg; print(pkg.__file__)"`.
- Is this the interpreter and environment? `sys.executable`, `pip list`/`uv pip list`.
- Is the code path reached? A temporary `raise` or breakpoint answers it at once.
- Is the input what you think? Log `repr()` and `type()`, not `str()`.

For repeated concurrency failures, question ownership of shared state rather than
adding another lock.

## Tools

- `pytest -x --lf -vv`, `pytest -k <expr>`, `pytest --pdb`, `-s` to see output,
  `--tb=long`, `-p no:cacheprovider` when caching is suspect.
- `breakpoint()` / `python -m pdb`; `PYTHONBREAKPOINT=0` disables leftovers.
- `python -X dev` and `-W error` surface resource and deprecation warnings.
- `python -X importtime`, `python -v` for import problems.
- `faulthandler` (`python -X faulthandler`, `faulthandler.dump_traceback_later`)
  for hangs and crashes; `py-spy dump --pid <pid>` if installed.
- `git bisect` when it used to work and a good commit is known.
- `tracemalloc` for leaks; `logging` at DEBUG for flows across components.

## Common Python causes

- Mutable default arguments; shared class-level mutable attributes.
- Late-binding closures in loops; iterating while mutating; exhausted generators.
- `is` vs `==`; truthiness of `0`, `""`, empty containers vs `None`.
- Naive vs aware datetimes; local time vs UTC; float equality.
- Shadowed modules (a local `json.py`, stale `.pyc`, editable install pointing elsewhere).
- Circular imports; import-time side effects; different results under `python -m`.
- Swallowed exceptions (`except Exception: pass`), exceptions lost in threads or
  un-awaited tasks.
- Async: blocking call in the event loop, missing `await`, task garbage-collected,
  cancellation swallowed, shared session across tasks.
- Tests: fixture scope leaking state, patching the wrong import path, order dependence.

## Do not

- Do not "fix" by wrapping in `try/except`, adding `sleep`, retries, or `or default`.
- Do not change several things at once and keep whatever went green.
- Do not edit the test to match the wrong behavior.
- Do not leave `print`, `breakpoint()`, or debug flags in the result.

## Report

State the root cause as a mechanism, the evidence for it, the fix, the regression
test, and any related risk you noticed but did not change.
