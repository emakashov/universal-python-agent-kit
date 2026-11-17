# AGENTS.md — Universal Agent Kit

Always-on instructions for AI coding agents. They apply to every engineering task;
the user's own skills (section 2) apply to every task of any kind.
A more specific instruction file in the repository, and any explicit user request,
take precedence over this file.

## 1. Precedence

1. The user's explicit request and acceptance criteria.
2. The repository's own instructions and existing conventions.
3. The user's own skills (Tier 0).
4. This file and the kit's skills.
5. General ecosystem recommendations.

The existing code, tests, configuration, and docs are the source of truth. Do not
replace a working project decision with a personal preference, and do not assume
tools, frameworks, or architecture the project does not have.

## 2. Skill system

Skills are organized in four tiers. A skill being present in the kit does not make
its technology mandatory for the project.

| Tier | Activation | Skills |
|------|------------|--------|
| 0. User Skills | **Always**, for every task of any kind, not only engineering | <!-- kit:user-skills -->none installed<!-- /kit:user-skills --> |
| 1. Engineering Core | **Always**, for every engineering task | `ub-engineering`, `ub-workflow`, `ub-quality-gates` |
| 2. Language & Engineering | By project language **and** task type | Python: `python-development`, `python-testing`, `python-debugging`, `python-code-review`, `python-refactoring`, `python-packaging`, `python-performance`, `python-security`, `python-documentation`, `python-data-engineering` |
| 3. Technology Specialists | **Only** if the technology is used in the project | `fastapi`, `django`, `sqlalchemy`, `postgresql`, `docker`, `ci-cd`, `machine-learning`, `observability` |

Tier 0 skills are the user's own. In the agent's skills directory they sit next to
the kit's skills and are not marked, so the table above is the authoritative list:
the installer writes it from `<!-- kit:user-skills-dir -->~/ai/user-skills/<!-- /kit:user-skills-dir -->`
at install time and links each skill into the agent's skills directory under the
same name. Re-run the installer after adding or removing a user skill.

Activation procedure, at the start of a task:

0. For every task, engineering or not, load every Tier 0 skill named in the table
   by name, through the agent's skill mechanism. Without one, read
   `<!-- kit:user-skills-dir -->~/ai/user-skills/<!-- /kit:user-skills-dir --><name>/SKILL.md`.
   If the table says "none installed", skip this step.
1. For an engineering task, load the three Tier 1 skills. They are language-independent.
2. Detect the project's languages from its manifests and sources
   (`pyproject.toml`, `requirements*.txt`, `*.py` → Python). Load the Tier 2 skills of
   that language that match the task: writing code → `*-development`; tests →
   `*-testing`; a failure → `*-debugging`; a review → `*-code-review`; and so on.
3. Detect technologies from dependencies and files, not from guesses. Load a Tier 3
   skill only when its technology is actually present or the user asks to add it.
4. If no language pack exists for the project's language, apply Tier 1 alone and
   follow that ecosystem's established conventions. Never apply Python-specific
   rules to non-Python code.

If your agent has no skill mechanism, read the files directly:
`skills/<pack>/<skill>/SKILL.md` inside the kit directory.

## 3. Engineering principles (summary of Tier 1)

These are adapted from Robert C. Martin's `ub-mode`. The full text is in `ub-engineering`.

- **Attack the premise.** After two failed attempts at fixing the same problem, stop
  patching the symptom. List the assumptions the approach rests on and test the
  weakest one. A third lock around shared state is rarely the answer; the ownership
  of that state usually is.
- **Test behavior, not implementation.** A test asserts what a user of the unit
  observes: return values, state visible through the public API, emitted effects.
  A test that mirrors the code's internal structure only proves that the code does
  what it does, including its bugs.
- **Subtract before you add.** Before adding a class, abstraction, config option, or
  dependency, check whether deleting or simplifying something solves the problem.
  Prefer the smallest change that fully solves the task.
- **TDD by default.** Write a failing test first for behavior changes and bug fixes.
  Do not invent artificial tests for trivial changes (renames, comments, config
  values, formatting).
- **Fix root causes.** Reproduce first, explain the mechanism, then fix. A fix you
  cannot explain is a guess.
- **Evidence before claims.** Never report that something works without having run
  the check that shows it. State what was verified, how, and what was not verified.

## 4. Autonomy and Git safety

- **Commit only when the user asks.** Push, force-push, merge, rebase of shared
  branches, tag, and release only with explicit, action-specific permission.
- Never push to the main branch on your own initiative.
- **Never delete the user's work automatically.** Do not run `git reset --hard`,
  `git clean`, `git checkout -- <path>`, `git stash drop`, or remove worktrees,
  branches, or untracked files unless the user asked for exactly that. If cleanup
  seems useful, list what would be removed and ask.
- Do not read, print, or commit secrets (`.env`, keys, tokens, credentials).
- Do not install tools or add dependencies without the user's agreement. Use the
  quality tools that are already installed; report the ones that are missing.
- Destructive or irreversible operations (data migrations, deletions, deployments)
  need explicit confirmation each time.

## 5. Quality gates (summary)

Run checks proportionate to the risk of the change, and only with tools the project
has installed. The full policy is in `ub-quality-gates`.

- Baseline: the project's tests, linter, formatter, and type checker.
- For risky or critical logic: coverage, complexity, CRAP score, duplication,
  mutation testing.
- Metrics are indicators, not proof. Target CRAP < 10 per function; justify
  exceptions rather than splitting a function artificially to please the metric.
  Check that duplication is actually harmful before removing it.

## 6. Language of code comments

- File has English comments → write new comments in English.
- File has Russian comments → write new comments in Russian.
- Both languages used about equally → prefer Russian.
- File has no comments → follow neighboring files; if the project has no convention,
  use Russian.
- Do not mass-translate existing comments without a reason.
- Never use the letter «ё» in comments; write «е» instead ("еще", not "ещё").
- No period at the end of a sentence or paragraph when nothing follows it or
  only a blank line does (paragraphs are separated by a blank line). Periods
  between sentences stay: `# Кэш сбрасывается вручную. Иначе тесты падают`

Identifiers, commit messages, and log messages follow the project's existing
convention (English when there is none).

## 7. Decision log and reporting

Record significant decisions and verifications, not every action: the chosen
approach and rejected alternatives, assumptions that were tested, checks that were
run and their results, known gaps. In the final report state plainly what changed,
what was verified, what failed, and what remains.
