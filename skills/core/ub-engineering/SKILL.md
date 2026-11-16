---
name: ub-engineering
description: Core engineering principles adapted from Robert C. Martin's ub-mode - attack the premise, test behavior not implementation, subtract before you add, root-cause analysis, simple design, and dependency direction. Use for every engineering task in any language - writing, changing, debugging, reviewing, or designing code.
---

# UB Engineering

Tier 1, always active, language-independent. These principles govern how decisions
are made; `ub-workflow` governs the order of work and `ub-quality-gates` governs
verification.

## 1. Attack the premise

Repeated failure usually means a wrong assumption, not an insufficient patch.

- **Trigger:** two attempts at the same problem have failed, or each fix surfaces a
  new failure of the same kind.
- **Stop editing.** Write down the assumptions the current approach depends on
  ("this function is only called from one thread", "the cache is always warm",
  "the test fixture matches production data").
- Pick the assumption that, if false, would explain the most evidence. Test it
  directly with an experiment, not with another fix.
- If the premise is wrong, change the design. Tell the user that the direction
  changed and why.

Example: tests for concurrent task processing keep failing after adding locks.
Do not add a third lock. Ask who owns the shared state and whether it needs to be
shared at all. Giving each worker its own state and merging results through a queue
removes the class of bug.

## 2. Test behavior, not implementation

- Assert what a caller observes: results, state reachable through the public API,
  messages sent to collaborators at a real boundary.
- Do not assert private attributes, call order of internal helpers, or the exact
  shape of intermediate data.
- Derive expected values from the requirement, never by copying them from the
  output of the code under test. Otherwise the test certifies the bug.
- A behavior test survives a refactoring unchanged. If a refactoring forces test
  edits, the tests were coupled to the implementation.

## 3. Subtract before you add

Before adding anything, ask in this order:

1. Can the problem be solved by deleting code, a branch, or a special case?
2. Can an existing function, type, or library feature already do it?
3. Can it be done by changing a few lines in place?
4. Only then: add new code, and add the least that works.

Do not add without a present need: abstract base classes with one implementation,
factories, plugin registries, configuration options, feature flags, wrappers around
a library, new dependencies, "just in case" parameters. Three similar lines are
better than a premature abstraction.

## 4. Root cause over symptom

- Reproduce the problem before changing code.
- Explain the mechanism from cause to observed effect. If a step is a guess, verify it.
- Fix the cause at the place where it originates. Do not hide it with broad
  `try/except`, retries, sleeps, default values, or relaxed assertions.
- Never weaken or delete a test to make it pass unless the test itself is wrong, and
  say so when it is.

## 5. Simple design

In priority order, code should: pass its tests, reveal intent, contain no harmful
duplication, and have the fewest elements.

- Functions do one thing at one level of abstraction; names say what, not how.
- Prefer plain data and functions; introduce a class when there is state with
  invariants to protect.
- Duplication is harmful when the copies must change together. Code that merely
  looks alike but changes for different reasons should stay separate.
- Leave code you touched cleaner than you found it, but keep unrelated cleanup out
  of the change.

## 6. Architecture and boundaries

- Dependencies point toward policy: business rules do not import frameworks, ORMs,
  HTTP clients, or the file system directly. Details depend on the core, not the reverse.
- Validate and convert data at the boundary (HTTP, CLI, files, queues, database);
  inside, work with already-valid typed values.
- One reason to change per module. Depend on narrow interfaces you own.
- Respect the architecture the project already has. Propose structural change;
  do not smuggle it into an unrelated task.

## 7. Honesty about results

- Do not claim success without evidence from a check you ran.
- Report failures, skipped steps, and unverified parts as plainly as successes.
- State uncertainty instead of presenting a guess as a fact.

## 8. Code comments

Write comments that explain why, not what. Language of new comments: match the
file (English → English, Russian → Russian); mixed about equally → Russian; no
comments → follow neighboring files, and Russian when the project has no
convention. Do not mass-translate existing comments.
