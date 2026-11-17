"""Тесты отбора файлов установщика по .gitignore комплекта.

Запуск: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import install  # noqa: E402


def make_tree(root: Path, files: list[str]) -> None:
    for rel in files:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rel, encoding="utf-8")


def listed(root: Path) -> set[str]:
    rules = install.IgnoreRules.load(root)
    return {p.as_posix() for p in install.iter_files(root, rules)}


class IterFilesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def kit(self, gitignore: str | None, files: list[str]) -> set[str]:
        if gitignore is not None:
            (self.root / ".gitignore").write_text(gitignore, encoding="utf-8")
        make_tree(self.root, files)
        return listed(self.root)

    def test_gitignore_itself_and_git_dir_are_not_copied(self) -> None:
        got = self.kit("", ["AGENTS.md", ".git/config"])
        self.assertEqual(got, {"AGENTS.md"})

    def test_without_gitignore_everything_but_git_is_copied(self) -> None:
        got = self.kit(None, ["AGENTS.md", ".idea/x.xml", ".git/HEAD"])
        self.assertEqual(got, {"AGENTS.md", ".idea/x.xml"})

    def test_name_pattern_matches_at_any_depth(self) -> None:
        got = self.kit(".idea\n", ["a.md", ".idea/w.xml", "skills/s/.idea/w.xml"])
        self.assertEqual(got, {"a.md"})

    def test_glob_pattern(self) -> None:
        got = self.kit("*.pyc\n", ["install.py", "tools/x.pyc", "x.pyc"])
        self.assertEqual(got, {"install.py"})

    def test_comments_and_blank_lines_are_ignored(self) -> None:
        got = self.kit("# .idea\n\n   \n", ["a.md", ".idea/w.xml"])
        self.assertEqual(got, {"a.md", ".idea/w.xml"})

    def test_trailing_slash_matches_only_directories(self) -> None:
        got = self.kit("build/\n", ["build/out.txt", "docs/build"])
        self.assertEqual(got, {"docs/build"})

    def test_leading_slash_anchors_to_kit_root(self) -> None:
        got = self.kit("/notes.md\n", ["notes.md", "skills/s/notes.md"])
        self.assertEqual(got, {"skills/s/notes.md"})

    def test_middle_slash_anchors_to_kit_root(self) -> None:
        got = self.kit("tools/tmp\n", ["tools/tmp/a", "x/tools/tmp/a", "tools/ok.py"])
        self.assertEqual(got, {"x/tools/tmp/a", "tools/ok.py"})

    def test_double_star_prefix(self) -> None:
        got = self.kit("**/cache/*.json\n", ["cache/a.json", "x/y/cache/b.json", "cache/c.txt"])
        self.assertEqual(got, {"cache/c.txt"})

    def test_negation_reincludes_a_file(self) -> None:
        got = self.kit("*.log\n!keep.log\n", ["a.log", "keep.log"])
        self.assertEqual(got, {"keep.log"})

    def test_files_in_ignored_directory_cannot_be_reincluded(self) -> None:
        # Так же ведет себя git: содержимое исключенного каталога не возвращается.
        got = self.kit("tmp/\n!tmp/keep.txt\n", ["tmp/keep.txt", "a.md"])
        self.assertEqual(got, {"a.md"})


class InstallCopyTest(unittest.TestCase):
    """Сквозная проверка: каталог установки не получает игнорируемых файлов."""

    def test_install_skips_gitignore_and_ignored_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            code = install.main(["--home", str(home), "--prefix", str(Path(tmp) / "ai"),
                                 "--agents", "codex", "--languages", "none", "--tech", "none",
                                 "--on-conflict", "skip"])
            self.assertEqual(code, 0)
            kit_home = Path(tmp) / "ai" / "agent-kit"
            installed = {p.relative_to(kit_home).as_posix() for p in kit_home.rglob("*") if p.is_file()}
            self.assertIn("AGENTS.md", installed)
            self.assertNotIn(".gitignore", installed)
            rules = install.IgnoreRules.load(install.KIT_SRC)
            leaked = {p for p in installed if rules.ignored_path(Path(p))}
            self.assertEqual(leaked, set())


if __name__ == "__main__":
    unittest.main()
