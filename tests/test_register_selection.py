"""Shared register ownership: CLI selection, explicit pre-install, target binding."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_doctor import install_wiring_block

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-09-11"


class RegisterSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="register-selection-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)

    def seed(self, relative, complete=True):
        path = self.project / relative
        path.mkdir(parents=True, exist_ok=True)
        (path / "STATUS.md").write_text(
            f"# STATUS\n\nLast updated: {TODAY}\n\n## In flight\n\n- Ship parser\n")
        (path / "CHANGELOG.md").write_text(
            f"# CHANGELOG\n\n## {TODAY} — initialized project documentation system\n\nInstalled.\n")
        if complete:
            (path / "DECISIONS.md").write_text("# DECISIONS\n")
        (path / "README.md").write_text("*Installed via the `project-docs-protocol` skill.*\n")
        return path

    def cli(self, tool, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / f"scripts/docs-{tool}.py"),
                               str(self.project), "--today", TODAY, *args],
                              capture_output=True, text=True, cwd=self.temp.name)

    def snapshot(self, path):
        return {str(p.relative_to(path)): p.read_bytes() for p in path.rglob("*") if p.is_file()}

    def assert_selected(self, relative, *args):
        (self.project / "AGENTS.md").write_text(install_wiring_block(relative))
        doctor = self.cli("doctor", "--no-git", *args)
        self.assertNotEqual(doctor.returncode, 3, doctor.stderr)
        self.assertRegex(doctor.stdout, r"(?m)^PASS\s+wiring-path\s")
        plan_path = self.project / "plan.json"
        result = self.cli("migrate", "--plan", str(plan_path), *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text())
        self.assertEqual(plan.get("register_dir"), str((self.project / relative).resolve()))
        for item in plan["mappings"]:
            item["reviewed"] = True
            item["row"]["closes_when"] = "Parser regression passes."
        plan_path.write_text(json.dumps(plan))
        result = self.cli("migrate", "--write", "--plan", str(plan_path), *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.project / relative / "LEDGER.md").is_file())

    def test_complete_root_wins_over_partial_docs(self):
        self.seed(".")
        other = self.seed("docs", complete=False)
        before = self.snapshot(other)
        self.assert_selected(".")
        self.assertEqual(before, self.snapshot(other))

    def test_root_only_and_unrelated_empty_docs(self):
        for empty in (False, True):
            with self.subTest(empty_docs=empty):
                self.seed(".")
                if empty:
                    (self.project / "docs").mkdir()
                self.assert_selected(".")
                # Subsequent iteration has a new source identity/plan receipt.
                for path in self.project.iterdir():
                    if path.is_file():
                        path.unlink()

    def test_docs_only(self):
        self.seed("docs")
        self.assert_selected("docs")

    def test_complete_docs_wins_over_partial_root(self):
        self.seed("docs")
        self.seed(".", complete=False)
        preserved = {n: (self.project / n).read_bytes() for n in ("STATUS.md", "CHANGELOG.md", "README.md")}
        self.assert_selected("docs")
        self.assertEqual(preserved, {n: (self.project / n).read_bytes() for n in preserved})
        self.assertFalse((self.project / "LEDGER.md").exists())

    def test_two_complete_require_explicit_selection_without_writes(self):
        self.seed(".")
        self.seed("docs")
        before = self.snapshot(self.project)
        for tool, code in (("doctor", 3), ("migrate", 2)):
            result = self.cli(tool)
            self.assertEqual(result.returncode, code, result.stdout + result.stderr)
            self.assertIn("--register-dir", result.stderr)
        self.assertEqual(before, self.snapshot(self.project))
        other = self.snapshot(self.project / "docs")
        self.assert_selected(".", "--register-dir", ".")
        self.assertEqual(other, self.snapshot(self.project / "docs"))

    def test_explicit_custom_register(self):
        self.seed("records")
        self.assert_selected("records", "--register-dir", "records")

    def test_preinstall_requires_explicit_directory_and_flag(self):
        docs = self.seed("docs", complete=False)
        before = self.snapshot(self.project)
        for args in ((), ("--register-dir", "docs"), ("--pre-install",)):
            result = self.cli("migrate", *args)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot(self.project))
        plan_path = self.project / "preinstall.json"
        args = ("--pre-install", "--register-dir", "docs", "--plan", str(plan_path))
        result = self.cli("migrate", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text())
        for item in plan["mappings"]:
            item["reviewed"] = True
            item["row"]["closes_when"] = "Parser regression passes."
        plan_path.write_text(json.dumps(plan))
        result = self.cli("migrate", *args, "--write")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((docs / "LEDGER.md").is_file())
        self.assertFalse((docs / "DECISIONS.md").exists())
        self.assertEqual(before["docs/STATUS.md"], (docs / "STATUS.md").read_bytes())

    def test_reviewed_plan_cannot_be_redirected_to_identical_register(self):
        self.seed(".")
        other = self.seed("docs")
        plan_path = self.project / "redirect.json"
        result = self.cli("migrate", "--register-dir", "docs", "--plan", str(plan_path))
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(plan_path.read_text())
        for item in plan["mappings"]:
            item["reviewed"] = True
            item["row"]["closes_when"] = "Parser regression passes."
        plan_path.write_text(json.dumps(plan))
        before = self.snapshot(self.project)
        result = self.cli("migrate", "--register-dir", ".", "--write", "--plan", str(plan_path))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("register", result.stderr)
        self.assertEqual(before, self.snapshot(self.project))
        self.assertFalse((other / "LEDGER.md").exists())
