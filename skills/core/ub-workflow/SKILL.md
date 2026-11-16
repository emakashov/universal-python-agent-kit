---
name: ub-workflow
description: Disciplined task workflow adapted from Robert C. Martin's ub-mode - understand, plan, TDD by default, small verified steps, decision log, and strict Git safety (commit only on request, push only with explicit permission, never delete user work). Use for every engineering task in any language, from the first read of the request to the final report.
---

# UB Workflow

Tier 1, always active, language-independent.

## 1. Understand before changing

- Restate the task as observable acceptance criteria. If a criterion is ambiguous
  and the choice matters, ask; otherwise choose the conventional option and say so.
- Read the code you will touch, its tests, and its callers. Find the project's
  commands for tests, lint, and types in its config or docs, and use those.
- Run the relevant tests before editing to know the baseline. Pre-existing failures
  are reported, not silently fixed or ignored.

## 2. Plan in small steps

Break the work into steps that each leave the code working and verifiable.
Prefer the order: make the change easy (refactor, tests green), then make the
easy change.

## 3. TDD by default

For behavior changes and bug fixes:

1. **Red.** Write one test that expresses the next piece of behavior and watch it
   fail for the expected reason.
2. **Green.** Write the least code that makes it pass.
3. **Refactor.** Remove duplication and clarify names with tests green.

For a bug: first write the test that reproduces it.

When not to write a test first: renames, comments, formatting, dependency bumps,
configuration values, generated code, exploratory spikes that will be discarded,
and glue with no logic. Do not manufacture a test that only restates the change.
When skipping TDD, say why and name the check that covers the change instead.

## 4. Verify each step

After each step run the narrowest relevant check; before reporting, run the full
set chosen per `ub-quality-gates`. If a check fails twice in the same way, apply
"attack the premise" from `ub-engineering` instead of trying a third variation.

## 5. Decision log

Record significant decisions and verifications, not every action:

- the approach chosen and the alternatives rejected, with the reason;
- assumptions tested and what the test showed;
- checks run, with their actual results;
- deviations from the request, known gaps, follow-ups.

Keep the log where the project keeps such notes (task file, PR description); if
there is no such place, include it in the final report. Do not create log files in
the repository unasked.

## 6. Git and workspace safety

These rules narrow the original ub-mode, which ends work by pushing to the main
branch and cleaning worktrees. An autonomous agent must not have that latitude.

| Action | Rule |
|--------|------|
| Edit files in scope | Allowed |
| `git add`, `git commit` | Only when the user asks |
| `git push`, open or merge a PR, tag, release | Only with explicit permission for that action |
| Push to main, force-push, rewrite published history | Never on own initiative |
| Delete branches, worktrees, stashes, untracked files; `reset --hard`, `clean`, `checkout -- <path>` | Never automatically; list what would be removed and ask |
| Changes by the user that are not yours | Leave untouched; never revert or reformat |

A permission covers the action it was given for and does not extend to later ones.
Before a commit, review the diff yourself: no secrets, no debug leftovers, no
unrelated files. Use the repository's commit message convention.

## 7. Scope discipline

- Change only what the task needs. Note unrelated problems in the report instead of
  fixing them.
- Do not add dependencies, tools, or services without agreement.
- Do not reformat files you are not otherwise changing.

## 8. Final report

State: what changed and where; what was verified and the result; what was not
verified or failed; decisions the user should know about; what remains.
