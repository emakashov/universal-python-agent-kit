"""Тесты подстановки списка пользовательских навыков в установленные инструкции

Агент не может отличить пользовательский навык от навыка комплекта в общем
каталоге навыков, поэтому установщик вписывает их имена в AGENTS.md и правило Cursor

Запуск: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import install  # noqa: E402

KIT_SRC = Path(install.__file__).resolve().parent


def write_skill(root: Path, name: str) -> None:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: d\n---\n", encoding="utf-8")


def tier0_row(text: str) -> str:
    return next(line for line in text.splitlines() if line.startswith("| 0. User Skills"))


class RenderedInstructionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name).resolve()
        self.home = base / "home"
        self.home.mkdir()
        self.prefix = self.home / "ai"
        self.user_dir = self.prefix / "user-skills"
        self.kit_home = self.prefix / "agent-kit"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def install(self, *extra: str) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = install.main(["--home", str(self.home), "--prefix", str(self.prefix),
                                 "--agents", "codex,cursor", "--languages", "none", "--tech", "none",
                                 "--on-conflict", "skip", *extra])
        self.assertEqual(code, 0, out.getvalue())
        return out.getvalue()

    def agents_md(self) -> str:
        return (self.kit_home / "AGENTS.md").read_text(encoding="utf-8")

    def test_tier0_row_names_installed_user_skills(self) -> None:
        write_skill(self.user_dir, "applear")
        write_skill(self.user_dir, "my-style")
        self.install()
        row = tier0_row(self.agents_md())
        self.assertIn("`applear`", row)
        self.assertIn("`my-style`", row)

    def test_agent_reads_the_list_through_its_instruction_link(self) -> None:
        write_skill(self.user_dir, "applear")
        self.install()
        linked = (self.home / ".codex" / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("`applear`", tier0_row(linked))

    def test_cursor_rule_names_user_skills(self) -> None:
        write_skill(self.user_dir, "applear")
        self.install("--project", str(self.home))
        rule = (self.home / ".cursor" / "rules" / "agent-kit-core.mdc").read_text(encoding="utf-8")
        user_line = next(line for line in rule.splitlines() if "**User skills.**" in line)
        self.assertIn("`applear`", user_line)

    def test_without_user_skills_the_row_says_none(self) -> None:
        self.install()
        row = tier0_row(self.agents_md())
        self.assertIn("none installed", row)
        self.assertNotIn("every skill in the user skills directory", row)

    def test_skill_clashing_with_kit_skill_is_not_listed(self) -> None:
        write_skill(self.user_dir, "ub-workflow")
        self.install()
        self.assertNotIn("`ub-workflow`", tier0_row(self.agents_md()))

    def test_user_directory_path_is_written_for_the_actual_prefix(self) -> None:
        self.prefix = self.home / "tools" / "ai"
        self.user_dir = self.prefix / "user-skills"
        self.kit_home = self.prefix / "agent-kit"
        self.install()
        self.assertIn("~/tools/ai/user-skills/", self.agents_md())

    def test_new_user_skill_updates_list_without_a_conflict(self) -> None:
        write_skill(self.user_dir, "applear")
        self.install()
        write_skill(self.user_dir, "my-style")
        output = self.install()
        self.assertIn("`my-style`", tier0_row(self.agents_md()))
        self.assertNotIn("skipped", output)

    def test_user_edit_outside_the_list_is_still_a_conflict(self) -> None:
        self.install()
        path = self.kit_home / "AGENTS.md"
        path.write_text(path.read_text(encoding="utf-8") + "my note\n", encoding="utf-8")
        write_skill(self.user_dir, "applear")
        self.install()
        self.assertIn("my note", self.agents_md())

    def test_project_scope_run_keeps_the_user_list(self) -> None:
        write_skill(self.user_dir, "applear")
        self.install()
        project = self.home / "proj"
        project.mkdir()
        self.install("--project", str(project))
        self.assertIn("`applear`", tier0_row(self.agents_md()))

    def test_source_template_is_not_modified(self) -> None:
        before = (KIT_SRC / "AGENTS.md").read_text(encoding="utf-8")
        write_skill(self.user_dir, "applear")
        self.install()
        self.assertEqual((KIT_SRC / "AGENTS.md").read_text(encoding="utf-8"), before)

    def test_dry_run_writes_nothing(self) -> None:
        write_skill(self.user_dir, "applear")
        self.install("--dry-run")
        self.assertFalse(self.kit_home.exists())


if __name__ == "__main__":
    unittest.main()
