#!/usr/bin/env python3
"""Installer for the Universal Agent Kit.

Copies the kit into an install directory (default ``~/ai/agent-kit``) and creates
symlinks in the places where coding agents discover skills and always-on
instructions. Existing content is never replaced silently: on a conflict the
installer asks what to do (overwrite, back up, skip, show diff, abort).

Standard library only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import difflib
import filecmp
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

KIT_SRC = Path(__file__).resolve().parent
# Never part of the installed kit: VCS data and the ignore file itself.
# Everything else that must not be copied is listed in the kit's .gitignore.
ALWAYS_IGNORED = {".git", ".gitignore"}
CONFLICT_MODES = ("ask", "overwrite", "backup", "skip", "abort")


class Abort(Exception):
    """The user chose to stop the installation."""


# --------------------------------------------------------------------------- utils


def load_manifest(root: Path) -> dict:
    with open(root / "kit.json", encoding="utf-8") as fh:
        return json.load(fh)


def _glob_to_regex(glob: str) -> str:
    """Translate one gitignore glob into a regex over a ``/``-separated path."""
    out, i, n = [], 0, len(glob)
    while i < n:
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("/**", i) and i + 3 == n:
            out.append("/.*")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        elif glob[i] == "[" and "]" in glob[i + 2:]:
            end = glob.index("]", i + 2)
            body = glob[i + 1:end]
            if body.startswith("!"):
                body = "^" + body[1:]
            out.append("[" + body.replace("\\", "\\\\") + "]")
            i = end + 1
        elif glob[i] == "\\" and i + 1 < n:
            out.append(re.escape(glob[i + 1]))
            i += 2
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return "".join(out)


class IgnoreRules:
    """The subset of gitignore syntax the installer needs.

    Supported: comments, blank lines, ``!`` negation, a trailing ``/`` for
    directories only, anchoring by a leading or inner ``/``, ``*``, ``?``,
    ``[...]``, and ``**``. Paths are matched relative to the walked root.
    """

    def __init__(self, lines: list[str]):
        self.rules: list[tuple[re.Pattern[str], bool, bool, bool]] = []
        for raw in lines:
            line = raw.rstrip("\n").rstrip()
            if not line or line.startswith("#"):
                continue
            negate = line.startswith("!")
            if negate:
                line = line[1:]
            elif line.startswith(("\\!", "\\#")):
                line = line[1:]
            dir_only = line.endswith("/")
            line = line.rstrip("/")
            if not line:
                continue
            anchored = "/" in line
            pattern = re.compile(_glob_to_regex(line.lstrip("/")) + r"\Z", re.DOTALL)
            self.rules.append((pattern, negate, dir_only, anchored))

    @classmethod
    def load(cls, root: Path) -> IgnoreRules:
        path = root / ".gitignore"
        if not path.is_file():
            return cls([])
        return cls(path.read_text(encoding="utf-8").splitlines())

    def ignored(self, rel: str, is_dir: bool) -> bool:
        """Decide for one path whose parent directories are already known to be kept."""
        name = rel.rsplit("/", 1)[-1]
        if name in ALWAYS_IGNORED:
            return True
        result = False
        for pattern, negate, dir_only, anchored in self.rules:
            if dir_only and not is_dir:
                continue
            if pattern.match(rel if anchored else name):
                result = not negate
        return result

    def ignored_path(self, rel: Path) -> bool:
        """Like ``ignored`` for a file, also checking every parent directory."""
        parts = rel.parts
        for depth in range(1, len(parts)):
            if self.ignored("/".join(parts[:depth]), is_dir=True):
                return True
        return self.ignored(rel.as_posix(), is_dir=False)


def iter_files(root: Path, rules: IgnoreRules):
    """Yield files under ``root`` relative to it, skipping paths that ``rules`` ignore.

    An ignored directory is not entered, so, as in git, nothing inside it
    can be re-included by a negated pattern.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        base = Path(dirpath).relative_to(root)
        dirnames[:] = sorted(d for d in dirnames if not rules.ignored((base / d).as_posix(), is_dir=True))
        for name in sorted(filenames):
            rel = base / name
            if not rules.ignored(rel.as_posix(), is_dir=False):
                yield rel


def same_content(a: Path, b: Path, rules: IgnoreRules) -> bool:
    if a.is_dir() and b.is_dir():
        files_a, files_b = set(iter_files(a, rules)), set(iter_files(b, rules))
        return files_a == files_b and all(filecmp.cmp(a / f, b / f, shallow=False) for f in files_a)
    if a.is_file() and b.is_file():
        return filecmp.cmp(a, b, shallow=False)
    return False


def describe(path: Path) -> str:
    if path.is_symlink():
        return f"symlink -> {os.readlink(path)}"
    if path.is_dir():
        return "directory"
    return "file"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)


def file_diff(existing: Path, new: Path, label: str) -> list[str]:
    return list(
        difflib.unified_diff(
            read_lines(existing), read_lines(new), f"existing/{label}", f"kit/{label}"
        )
    )


def build_diff(existing: Path, new: Path, rules: IgnoreRules) -> str:
    """Describe how ``existing`` differs from the kit's ``new``, like ``diff -ru``."""
    out: list[str] = []
    if existing.is_symlink():
        out.append(f"Existing path is a symlink -> {os.readlink(existing)}\n")
        if not existing.exists():
            return "".join(out) + "(the link is broken)\n"
    if existing.is_file() and new.is_file():
        out += file_diff(existing, new, new.name) or ["(contents are identical)\n"]
    elif existing.is_dir() and new.is_dir():
        old_files, new_files = set(iter_files(existing, rules)), set(iter_files(new, rules))
        for rel in sorted(old_files | new_files):
            if rel not in new_files:
                out.append(f"Only in existing: {rel}\n")
            elif rel not in old_files:
                out.append(f"Only in kit: {rel}\n")
            else:
                out += file_diff(existing / rel, new / rel, str(rel))
    else:
        out.append(f"Type differs: existing is a {describe(existing)}, kit provides a {describe(new)}\n")
    return "".join(out) or "(no differences)\n"


# ------------------------------------------------------------------ conflict handling


class Installer:
    def __init__(self, mode: str, backup_dir: Path, dry_run: bool, interactive: bool,
                 rules: IgnoreRules):
        self.mode = mode
        self.rules = rules
        self.backup_dir = backup_dir
        self.dry_run = dry_run
        self.interactive = interactive
        self.counts: dict[str, int] = {}
        self.warned_noninteractive = False

    def log(self, status: str, path: Path, note: str = "") -> None:
        self.counts[status] = self.counts.get(status, 0) + 1
        suffix = f"  ({note})" if note else ""
        print(f"  {status:<9} {path}{suffix}")

    def resolve_conflict(self, src: Path, dst: Path) -> str:
        """Return 'overwrite', 'backup', or 'skip'. Raise Abort to stop."""
        if self.mode == "abort":
            raise Abort(f"{dst} already exists and differs from the kit version")
        if self.mode != "ask":
            return self.mode
        if not self.interactive:
            if not self.warned_noninteractive:
                print("  note: no terminal for questions; keeping existing content "
                      "(use --on-conflict to choose another policy)")
                self.warned_noninteractive = True
            return "skip"
        print(f"\nConflict: {dst}")
        print(f"  existing: {describe(dst)}; it differs from the kit version {src}")
        while True:
            print("  [o] overwrite   [b] back up, then install   [s] skip (keep existing)")
            print("  [d] show diff   [a] abort installation")
            print('  Add "!" to apply the choice to all remaining conflicts, e.g. "b!"')
            try:
                answer = input("  Choice [s]: ").strip().lower() or "s"
            except EOFError:
                answer = "s"
            sticky = answer.endswith("!")
            choice = {"o": "overwrite", "b": "backup", "s": "skip", "d": "diff", "a": "abort"}.get(
                answer.rstrip("!")
            )
            if choice == "diff":
                print(build_diff(dst, src, self.rules))
            elif choice == "abort":
                raise Abort("stopped at the user's request")
            elif choice:
                if sticky:
                    self.mode = choice
                return choice
            else:
                print("  Unknown answer.")

    def backup(self, dst: Path) -> Path:
        # Backups live outside agent directories so that a saved skill is not
        # discovered by the agent as a second copy.
        target = self.backup_dir / str(dst.parent.resolve()).lstrip(os.sep) / dst.name
        if not self.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst), str(target))
        return target

    def remove(self, dst: Path) -> None:
        if self.dry_run:
            return
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)

    def create(self, src: Path, dst: Path, link: bool) -> None:
        if self.dry_run:
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        if link:
            os.symlink(src, dst, target_is_directory=src.is_dir())
        elif src.is_dir():
            for rel in iter_files(src, self.rules):
                (dst / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src / rel, dst / rel)
        else:
            shutil.copy2(src, dst)

    def place(self, src: Path, dst: Path, link: bool, content: Path | None = None) -> None:
        """Install ``src`` at ``dst`` as a symlink or a copy, never clobbering silently.

        ``content`` is the path used for comparison when ``src`` does not exist yet
        (dry run before the kit is copied).
        """
        ref = content if content is not None and not src.exists() else src
        exists = os.path.lexists(dst)
        if not exists:
            self.create(src, dst, link)
            self.log("linked" if link else "copied", dst)
            return
        if dst.is_symlink() and dst.exists() and dst.resolve() == src.resolve():
            self.log("ok", dst)
            return
        if dst.is_symlink() and not dst.exists():
            # A dangling link holds no content, so replacing it loses nothing.
            stale = os.readlink(dst)
            self.remove(dst)
            self.create(src, dst, link)
            self.log("linked" if link else "copied", dst, f"replaced broken link -> {stale}")
            return
        if not dst.is_symlink() and same_content(dst, ref, self.rules):
            if link:  # an identical copy: replacing it with a link loses nothing
                self.remove(dst)
                self.create(src, dst, link)
                self.log("linked", dst, "replaced identical copy")
            else:
                self.log("ok", dst)
            return
        action = self.resolve_conflict(ref, dst)
        if action == "skip":
            self.log("skipped", dst, "existing content kept")
            return
        if action == "backup":
            saved = self.backup(dst)
            note = f"backup: {saved}"
        else:
            self.remove(dst)
            note = "overwritten"
        self.create(src, dst, link)
        self.log("linked" if link else "copied", dst, note)


# ----------------------------------------------------------------- stack detection


def read_dependency_text(project: Path, patterns: list[str]) -> str:
    chunks = []
    for pattern in patterns:
        for path in sorted(project.glob(pattern)):
            if path.is_file() and path.stat().st_size < 2_000_000:
                chunks.append(path.read_text(encoding="utf-8", errors="replace").lower())
    return "\n".join(chunks)


def detected(rule: dict | None, project: Path, dep_text: str) -> bool:
    if not rule:
        return False
    for pattern in rule.get("files", []):
        if any(True for _ in project.glob(pattern)):
            return True
    for dep in rule.get("deps", []):
        if re.search(rf"(?<![\w-]){re.escape(dep.lower())}(?![\w-])", dep_text):
            return True
    return any(word.lower() in dep_text for word in rule.get("content", []))


def parse_choice(value: str, available: list[str], what: str) -> list[str]:
    names = [v.strip() for v in value.split(",") if v.strip()]
    unknown = [n for n in names if n not in available]
    if unknown:
        sys.exit(f"error: unknown {what}: {', '.join(unknown)} (available: {', '.join(available)})")
    return names


def select_skills(manifest: dict, languages: str, tech: str, project: Path | None):
    """Return (languages, [(skill name, path relative to the kit root)])."""
    packs = manifest["packs"]
    language_packs = [name for name, p in packs.items() if p["kind"] == "language"]
    dep_text = read_dependency_text(project, manifest.get("dependency_files", [])) if project else ""

    if languages == "all" or (languages == "auto" and project is None):
        chosen_langs = language_packs
    elif languages == "auto":
        chosen_langs = [n for n in language_packs if detected(packs[n].get("detect"), project, dep_text)]
    elif languages == "none":
        chosen_langs = []
    else:
        chosen_langs = parse_choice(languages, language_packs, "language")

    selected: list[tuple[str, str]] = []
    tech_names = [s for p in packs.values() if p["kind"] == "technology" for s in p["skills"]]
    explicit_tech = None if tech in ("auto", "all", "none") else parse_choice(tech, tech_names, "technology skill")

    for pack_name, pack in packs.items():
        for skill, meta in pack["skills"].items():
            rel = f"{pack['path']}/{skill}"
            if pack["kind"] == "core":
                take = True
            elif pack["kind"] == "language":
                take = pack_name in chosen_langs
            elif explicit_tech is not None:
                take = skill in explicit_tech
            elif tech == "none":
                take = False
            else:
                langs_ok = not meta.get("languages") or bool(set(meta["languages"]) & set(chosen_langs))
                if tech == "all" or project is None:
                    take = langs_ok
                else:
                    take = langs_ok and detected(meta.get("detect"), project, dep_text)
            if take:
                selected.append((skill, rel))
    return chosen_langs, selected


# ------------------------------------------------------------------------ targets


def expand(path: str, home: Path, project: Path | None) -> Path:
    if path.startswith("~/"):
        return home / path[2:]
    return (project or home) / path


def select_agents(manifest: dict, value: str, home: Path) -> list[str]:
    agents = manifest["agents"]
    if value == "all":
        return list(agents)
    if value == "auto":
        found = [n for n, a in agents.items() if expand(a["marker"], home, None).exists()]
        if not found:
            print("No agent configuration directories detected; installing for all known agents.")
        return found or list(agents)
    return parse_choice(value, list(agents), "agent")


def ask_prefix(default: Path) -> Path:
    print(f"The kit will be installed to {default}")
    try:
        answer = input("Press Enter to accept, or type another directory: ").strip()
    except EOFError:
        answer = ""
    # "y" is a natural reply to a confirmation; it must not become a directory named "y".
    if answer.lower() in ("", "y", "yes", "д", "да"):
        return default
    return Path(answer).expanduser()


# ----------------------------------------------------------------------- commands


def cmd_list(manifest: dict) -> None:
    print(f"{manifest['name']} {manifest['version']}\n")
    for name, pack in manifest["packs"].items():
        print(f"Tier {pack['tier']} - {name} ({pack['kind']})")
        for skill, meta in pack["skills"].items():
            langs = f"  [{', '.join(meta['languages'])}]" if meta.get("languages") else ""
            print(f"  {skill}{langs}")
    print("\nAgents:")
    for name, agent in manifest["agents"].items():
        print(f"  {name:<8} {agent['title']}")


def cmd_uninstall(manifest: dict, kit_home: Path, home: Path, project: Path | None, dry_run: bool) -> None:
    scope = "project" if project else "user"
    removed = 0
    kit_real = kit_home.resolve()
    for agent in manifest["agents"].values():
        cfg = agent.get(scope, {})
        candidates: list[Path] = [expand(p, home, project) for p in cfg.get("files", {})]
        skills_dir = expand(cfg["skills"], home, project) if cfg.get("skills") else None
        if skills_dir and skills_dir.is_dir():
            candidates += sorted(skills_dir.iterdir())
        for path in candidates:
            if not path.is_symlink():
                continue
            target = Path(os.path.realpath(path))
            if target == kit_real or kit_real in target.parents:
                print(f"  removed   {path}")
                removed += 1
                if not dry_run:
                    path.unlink()
    print(f"\n{removed} symlink(s) removed{' (dry run)' if dry_run else ''}. "
          f"Copies made with --copy and the kit directory {kit_home} are left in place.")


def cmd_install(args, manifest: dict, kit_home: Path, home: Path, project: Path | None) -> int:
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_dir = kit_home.parent / f"{kit_home.name}-backups" / stamp
    rules = IgnoreRules.load(KIT_SRC)
    inst = Installer(args.on_conflict, backup_dir, args.dry_run, interactive, rules)

    languages, skills = select_skills(manifest, args.languages, args.tech, project)
    agents = select_agents(manifest, args.agents, home)
    scope = "project" if project else "user"

    print(f"Kit directory : {kit_home}")
    print(f"Scope         : {scope}{f' ({project})' if project else ''}")
    print(f"Agents        : {', '.join(agents)}")
    print(f"Languages     : {', '.join(languages) or 'none detected (core only)'}")
    print(f"Skills        : {', '.join(name for name, _ in skills)}")
    if args.dry_run:
        print("Dry run: nothing will be changed.")

    try:
        if KIT_SRC != kit_home.resolve():
            print(f"\n[1/2] Copying the kit to {kit_home}")
            for rel in iter_files(KIT_SRC, rules):
                inst.place(KIT_SRC / rel, kit_home / rel, link=False)
        else:
            print("\n[1/2] Running from the install directory; nothing to copy")

        print(f"\n[2/2] {'Copying' if args.copy else 'Linking'} skills and instructions")
        link = not args.copy
        done: set[Path] = set()
        for agent_name in agents:
            cfg = manifest["agents"][agent_name].get(scope, {})
            items: list[tuple[Path, str]] = []
            if cfg.get("skills"):
                skills_dir = expand(cfg["skills"], home, project)
                items += [(skills_dir / name, rel) for name, rel in skills]
            if not args.no_instructions:
                items += [(expand(dst, home, project), rel) for dst, rel in cfg.get("files", {}).items()]
            for dst, rel in items:
                if dst in done:
                    continue
                done.add(dst)
                inst.place(kit_home / rel, dst, link=link, content=KIT_SRC / rel)
    except Abort as exc:
        print(f"\nInstallation aborted: {exc}")
        print("Changes made before this point were kept; re-run the installer to continue.")
        return 2

    summary = ", ".join(f"{count} {status}" for status, count in sorted(inst.counts.items()))
    print(f"\nDone: {summary}{' (dry run)' if args.dry_run else ''}.")
    if inst.counts.get("skipped"):
        print("Skipped items keep their existing content. Re-run with "
              "--on-conflict backup (or answer interactively) to replace them.")
    if backup_dir.exists():
        print(f"Backups: {backup_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the Universal Agent Kit and link it into coding agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python3 install.py                         install to ~/ai/agent-kit, link for detected agents\n"
            "  python3 install.py --prefix ~/tools/ai     choose another install location\n"
            "  python3 install.py --project .             link into a project, skills chosen by its stack\n"
            "  python3 install.py --dry-run               show what would happen\n"
            "  python3 install.py --uninstall             remove the links again\n"
        ),
    )
    parser.add_argument("--prefix", help="parent directory for the kit (default: ~/ai, or $AGENT_KIT_PREFIX)")
    parser.add_argument("--project", metavar="DIR", help="link into this project instead of the user's home")
    parser.add_argument("--agents", default="auto", help="auto (default), all, or a comma-separated list")
    parser.add_argument("--languages", default="auto",
                        help="auto (default), all, none, or a comma-separated list of language packs")
    parser.add_argument("--tech", default="auto",
                        help="auto (default), all, none, or a comma-separated list of technology skills")
    parser.add_argument("--on-conflict", choices=CONFLICT_MODES, default="ask",
                        help="what to do when a target exists and differs (default: ask)")
    parser.add_argument("--copy", action="store_true", help="copy into agent directories instead of symlinking")
    parser.add_argument("--no-instructions", action="store_true",
                        help="link skills only, not the always-on instruction files")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without changing anything")
    parser.add_argument("--uninstall", action="store_true", help="remove symlinks that point into the kit")
    parser.add_argument("--list", action="store_true", help="list packs, skills, and supported agents")
    parser.add_argument("--home", help=argparse.SUPPRESS)  # for tests: stand-in for the home directory
    args = parser.parse_args(argv)

    manifest = load_manifest(KIT_SRC)
    if args.list:
        cmd_list(manifest)
        return 0

    home = Path(args.home).expanduser().resolve() if args.home else Path.home()
    project = Path(args.project).expanduser().resolve() if args.project else None
    if project and not project.is_dir():
        sys.exit(f"error: project directory not found: {project}")

    prefix_value = args.prefix or os.environ.get("AGENT_KIT_PREFIX")
    if prefix_value:
        prefix = Path(prefix_value).expanduser()
    else:
        prefix = home / "ai"
        asking = sys.stdin.isatty() and sys.stdout.isatty() and not args.uninstall
        if asking and KIT_SRC.parent != prefix.resolve():
            kit_default = prefix / manifest["install_dir_name"]
            chosen = ask_prefix(kit_default)
            if chosen != kit_default:
                return run(args, manifest, chosen.resolve(), home, project)
    return run(args, manifest, (prefix / manifest["install_dir_name"]).resolve(), home, project)


def run(args, manifest: dict, kit_home: Path, home: Path, project: Path | None) -> int:
    if args.uninstall:
        cmd_uninstall(manifest, kit_home, home, project, args.dry_run)
        return 0
    return cmd_install(args, manifest, kit_home, home, project)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
