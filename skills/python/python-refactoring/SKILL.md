---
name: python-refactoring
description: Safe, behavior-preserving refactoring of Python code - characterization tests, small reversible steps, removing harmful duplication, reducing complexity, and untangling dependencies. Use when restructuring, simplifying, renaming, extracting, or cleaning up Python code without changing what it does, or when preparing code for a feature.
---

# Python Refactoring

Tier 2. Refactoring changes structure, never behavior. If behavior must change,
that is a separate step with its own test.

## Preconditions

1. **Tests first.** The code to be changed must be covered by behavior tests that
   pass. If it is not, write characterization tests: capture what the code does
   now through its public interface, including odd cases, before changing it.
2. **Green baseline.** Run the tests and record the result before the first edit.
3. **Clear goal.** Name the specific problem (this function mixes parsing and I/O;
   these two modules must change together). "Cleaner" is not a goal.

## Procedure

- One small transformation at a time: rename, extract function, inline, move,
  replace conditional with dispatch, introduce parameter object.
- Run the tests after each transformation. If they fail, undo the step in your
  editor and take a smaller one. Do not debug forward through a broken refactoring.
- Tests should not need editing. If they do, either the step changed behavior or
  the tests are coupled to implementation; fix the test coupling as its own step.
- Keep refactoring and behavior change in separate, reviewable steps (and separate
  commits when the user asks for commits).

## Subtract first

Before restructuring, look for what can be deleted: dead code, unused parameters
and options, unreachable branches, wrappers that only forward, abstractions with
one implementation, compatibility code for versions no longer supported. Confirm
that code is unused by searching for all references, including dynamic ones
(`getattr`, string names in config, entry points, templates, serializers).

## Duplication

Similarity is a prompt to look, not an instruction to merge (see `ub-quality-gates`).

- Merge when the copies encode the same rule and must change together.
- Leave it when the resemblance is coincidental or the copies belong to different
  contexts that will diverge.
- A shared helper that needs flags to serve both callers is worse than the duplication.

## Complexity

- Reduce nesting with guard clauses and early returns.
- Split a function where the abstraction level changes, not at arbitrary line counts.
- Replace long `if/elif` on a type or key with a mapping or `match` when the cases
  are uniform; keep an explicit chain when they are not.
- Do not fragment one cohesive algorithm into many tiny functions to improve a
  complexity or CRAP score. State the exception instead.

## Python specifics

- Preserve public names; when moving them, leave a re-export and deprecate it
  only if the project wants that.
- Renames must cover string references: `__all__`, entry points, Django app
  labels and migrations, Celery task names, pickled class paths, log queries.
- Changing a signature: update every caller; use keyword-only arguments to make
  later changes safer.
- Use the type checker as a refactoring safety net: run it after each move or
  signature change.
- Do not reformat or re-sort untouched files; it buries the real change.

## Stop conditions

Stop and report when: the baseline is not green, coverage of the target is
insufficient and cannot be added cheaply, the refactoring needs a public API or
schema change, or the scope grows beyond what was asked.

## Report

What structural problem was addressed, the transformations applied, the evidence
that behavior is unchanged (same tests, same results), and anything left undone.
