"""Тесты подключения пользовательских навыков из каталога user-skills рядом с комплектом

Запуск: python3 -m unittest discover -s tests
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import install  # noqa: E402


def write_skill(root: Path, name: str, description: str = "d") -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\n---\n",
                                    encoding="utf-8")
    return skill


class UserSkillsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name).resolve()
        self.home = base / "home"
        self.home.mkdir()
        self.prefix = base / "ai"
        self.user_dir = self.prefix / "user-skills"
        self.skills_dir = self.home / ".agents" / "skills"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_installer(self, *extra: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = install.main(["--home", str(self.home), "--prefix", str(self.prefix),
                                 "--agents", "codex", "--languages", "none", "--tech", "none",
                                 "--on-conflict", "skip", *extra])
        return code, out.getvalue()

    def run_list(self) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = install.main(["--home", str(self.home), "--prefix", str(self.prefix), "--list"])
        self.assertEqual(code, 0)
        return out.getvalue()

    def test_list_shows_user_skills_as_tier_0(self) -> None:
        write_skill(self.user_dir, "my-style")
        output = self.run_list()
        tier0 = output.index("Tier 0")
        self.assertLess(tier0, output.index("Tier 1"))
        self.assertIn(str(self.user_dir), output[tier0:output.index("Tier 1")])
        self.assertIn("my-style", output[tier0:output.index("Tier 1")])

    def test_list_marks_user_skill_that_clashes_with_kit_skill(self) -> None:
        write_skill(self.user_dir, "ub-workflow")
        output = self.run_list()
        tier0 = output[output.index("Tier 0"):output.index("Tier 1")]
        self.assertIn("ub-workflow", tier0)
        self.assertIn("same name as a kit skill", tier0)

    def test_list_without_user_directory_says_none_and_creates_nothing(self) -> None:
        output = self.run_list()
        self.assertIn("(none)", output[output.index("Tier 0"):output.index("Tier 1")])
        self.assertFalse(self.user_dir.exists())

    def test_dry_run_details_user_skills(self) -> None:
        write_skill(self.user_dir, "my-style", "Answer tersely in Russian")
        write_skill(self.user_dir, "ub-workflow")
        (self.user_dir / "notes").mkdir()
        _, output = self.run_installer("--dry-run")
        lines = output.splitlines()

        def line_of(name: str) -> str:
            return next(line for line in lines if line.split()[:1] == [name])

        self.assertIn("Answer tersely in Russian", line_of("my-style"))
        self.assertIn(str(self.user_dir / "my-style"), output)
        self.assertIn("no SKILL.md", line_of("notes"))
        self.assertIn("same name as a kit skill", line_of("ub-workflow"))

    def test_details_are_printed_only_in_dry_run(self) -> None:
        write_skill(self.user_dir, "my-style", "Answer tersely in Russian")
        _, output = self.run_installer()
        self.assertNotIn("Answer tersely in Russian", output)

    def test_user_skill_is_linked_into_agent_skills(self) -> None:
        src = write_skill(self.user_dir, "my-style")
        code, _ = self.run_installer()
        self.assertEqual(code, 0)
        dst = self.skills_dir / "my-style"
        self.assertTrue(dst.is_symlink())
        self.assertEqual(dst.resolve(), src)

    def test_directory_without_skill_md_is_not_linked(self) -> None:
        (self.user_dir / "notes").mkdir(parents=True)
        self.run_installer()
        self.assertFalse(os.path.lexists(self.skills_dir / "notes"))

    def test_missing_user_directory_is_created_empty(self) -> None:
        code, _ = self.run_installer()
        self.assertEqual(code, 0)
        self.assertTrue(self.user_dir.is_dir())
        self.assertEqual(list(self.user_dir.iterdir()), [])

    def test_dry_run_does_not_create_user_directory(self) -> None:
        self.run_installer("--dry-run")
        self.assertFalse(self.user_dir.exists())

    def test_project_scope_does_not_link_user_skills(self) -> None:
        # Ссылка на личный каталог внутри проекта попала бы в его репозиторий
        write_skill(self.user_dir, "my-style")
        project = self.home / "proj"
        project.mkdir()
        self.run_installer("--project", str(project))
        self.assertFalse(os.path.lexists(project / ".agents" / "skills" / "my-style"))
        self.assertTrue((project / ".agents" / "skills" / "ub-engineering").is_symlink())

    def test_name_clash_with_kit_skill_keeps_kit_skill(self) -> None:
        write_skill(self.user_dir, "ub-engineering")
        _, output = self.run_installer()
        dst = self.skills_dir / "ub-engineering"
        self.assertEqual(dst.resolve(), (self.prefix / "agent-kit" / "skills/core/ub-engineering").resolve())
        self.assertIn("ub-engineering", output)
        self.assertIn("same name", output)

    def test_uninstall_removes_user_skill_links_but_keeps_skills(self) -> None:
        src = write_skill(self.user_dir, "my-style")
        self.run_installer()
        self.run_installer("--uninstall")
        self.assertFalse(os.path.lexists(self.skills_dir / "my-style"))
        self.assertTrue((src / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
