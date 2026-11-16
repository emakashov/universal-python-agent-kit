#!/usr/bin/env python3
"""Check that the kit is internally consistent. Run after adding or changing skills.

Verifies that every skill listed in kit.json exists with valid frontmatter, that
no skill directory is missing from kit.json, that skill names are unique across
packs, and that every file an agent links to exists. Standard library only.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KINDS = {"core", "language", "technology"}


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fields = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            fields[key.strip()] = value.strip()
    return fields


def main() -> int:
    manifest = json.loads((ROOT / "kit.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    seen: dict[str, str] = {}
    languages = {name for name, pack in manifest["packs"].items() if pack.get("kind") == "language"}

    for pack_name, pack in manifest["packs"].items():
        if pack.get("kind") not in KINDS:
            errors.append(f"pack {pack_name}: kind must be one of {sorted(KINDS)}")
        pack_dir = ROOT / pack["path"]
        if not pack_dir.is_dir():
            errors.append(f"pack {pack_name}: directory {pack['path']} not found")
            continue
        on_disk = {p.name for p in pack_dir.iterdir() if p.is_dir()}
        for extra in sorted(on_disk - set(pack["skills"])):
            errors.append(f"{pack['path']}/{extra}: directory is not listed in kit.json")
        for skill, meta in pack["skills"].items():
            where = f"{pack['path']}/{skill}"
            if skill in seen:
                errors.append(f"{where}: name already used in pack {seen[skill]}; agents need unique names")
            seen[skill] = pack_name
            if not NAME_RE.match(skill) or len(skill) > 64:
                errors.append(f"{where}: name must be lowercase letters, digits, hyphens, at most 64 characters")
            for lang in meta.get("languages", []):
                if lang not in languages:
                    errors.append(f"{where}: unknown language pack '{lang}'")
            skill_file = pack_dir / skill / "SKILL.md"
            if not skill_file.is_file():
                errors.append(f"{where}: SKILL.md not found")
                continue
            text = skill_file.read_text(encoding="utf-8")
            fields = frontmatter(text)
            if fields.get("name") != skill:
                errors.append(f"{where}: frontmatter name '{fields.get('name')}' must equal the directory name")
            description = fields.get("description", "")
            if not description:
                errors.append(f"{where}: frontmatter description is missing")
            elif len(description) > 1024:
                errors.append(f"{where}: description is {len(description)} characters (limit 1024)")
            if len(text.splitlines()) > 500:
                errors.append(f"{where}: SKILL.md exceeds 500 lines; move detail into reference files")

    for agent_name, agent in manifest["agents"].items():
        for scope in ("user", "project"):
            for dst, src in agent.get(scope, {}).get("files", {}).items():
                if not (ROOT / src).exists():
                    errors.append(f"agent {agent_name}/{scope}: source {src} for {dst} not found")

    for error in errors:
        print(f"ERROR {error}")
    print(f"{len(seen)} skills in {len(manifest['packs'])} packs, {len(manifest['agents'])} agents: "
          f"{'OK' if not errors else f'{len(errors)} error(s)'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
