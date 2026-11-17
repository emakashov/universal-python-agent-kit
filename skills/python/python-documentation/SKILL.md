---
name: python-documentation
description: Python documentation - docstrings, code comments and their language, README files, API reference, changelogs, and keeping docs consistent with code. Use when writing or updating docstrings, comments, README, usage guides, or API docs in a Python project, or when a code change makes existing documentation wrong.
---

# Python Documentation

Tier 2. Documentation is part of the change: when behavior changes, update the
docs that describe it in the same piece of work.

## Principles

- Write for a reader who has not seen the code or the conversation.
- Document what the code cannot say: purpose, contract, constraints, reasons,
  trade-offs. Do not restate the code.
- Wrong documentation is worse than none. Verify every command and example by
  running it, or mark it as not verified.
- Follow the project's existing docstring style, tooling, and language.

## Language of comments

- English comments in the file → new comments in English.
- Russian comments in the file → new comments in Russian.
- Both used about equally → prefer Russian.
- No comments in the file → follow neighboring files; with no project
  convention, use Russian.
- Do not mass-translate existing comments without a reason.
- Never use the letter «ё» in comments or docstrings; write «е» instead
  ("еще", not "ещё").
- No period at the end of a sentence or paragraph when nothing follows it or
  only a blank line does (paragraphs are separated by a blank line). Periods
  between sentences stay: `# Кэш сбрасывается вручную. Иначе тесты падают`

Docstrings follow the same rule unless the project publishes API docs in a
specific language. User-facing docs (README, guides) use the language the
project already uses for them.

## Comments

- Explain why: a non-obvious constraint, a workaround with a link to its cause,
  an invariant, a deliberate deviation.
- No comments that narrate the next line, record history ("fixed bug", "added by"),
  or keep dead code. Version control holds history.
- `TODO` only with an owner or issue reference, if the project allows TODOs.

## Docstrings

Public modules, classes, functions, and methods get a docstring; private helpers
only when not obvious. Use the style already in the project (Google, NumPy, or
reST); Google style when there is none.

```python
def parse_window(spec: str, *, tz: tzinfo = UTC) -> TimeWindow:
    """Parse a time window such as ``"09:00-17:30"``

    Args:
        spec: Start and end in 24-hour ``HH:MM-HH:MM`` form
        tz: Timezone both ends are interpreted in

    Returns:
        The window. An end earlier than the start means it crosses midnight

    Raises:
        ValueError: If ``spec`` is not in the expected form
    """
```

- First line: one sentence, imperative mood, what it does.
- Do not repeat types that are in the annotations.
- State units, timezones, mutability, ordering guarantees, side effects, and
  which exceptions callers should expect.
- Examples in docstrings should be runnable as doctests where the project runs them.

## README

A README answers, in order: what this is and for whom; how to install; the
shortest working example; configuration; how to develop and test; where to get
help; license. Keep it current and short; move depth into `docs/`.

## API and reference docs

- Generate reference from docstrings with the project's tool (Sphinx, MkDocs with
  mkdocstrings); do not hand-maintain a copy.
- For HTTP APIs the schema (OpenAPI) is the reference: keep models, descriptions,
  and examples accurate at the source.
- Build the docs if the project has a docs build, and fix warnings you introduced.

## Changelog

If the project keeps one, add an entry for user-visible changes in its existing
format (commonly Keep a Changelog: Added, Changed, Deprecated, Removed, Fixed,
Security). Describe the effect for the user, not the implementation.
