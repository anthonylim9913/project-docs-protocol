"""Reservation discovery must fail closed before planning or writing."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/docs-migrate.py"


class MigrationInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.docs = self.root / "docs"
        self.docs.mkdir()
        (self.docs / "STATUS.md").write_text("# STATUS\n\n## Known issues\n\n- Repair cache misses.\n")
        (self.docs / "CHANGELOG.md").write_text("# CHANGELOG\n")
        (self.docs / "DECISIONS.md").write_text("# DECISIONS\n")
        self.plan = self.root / "plan.json"

    def cli(self, *arguments):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.root),
                               "--today", "2026-10-27", "--plan", str(self.plan), *arguments],
                              capture_output=True, text=True, timeout=10)

    def reviewed_plan(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        plan = json.loads(self.plan.read_text())
        for mapping in plan["mappings"]:
            mapping["reviewed"] = True
            mapping["row"]["closes_when"] = "The cache fixture passes."
        self.plan.write_text(json.dumps(plan))

    def refused(self):
        for arguments in (("--plan", str(self.root / "fresh.json")), ("--write",)):
            with self.subTest(arguments=arguments):
                result = self.cli(*arguments)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse((self.docs / "LEDGER.md").exists())

    def test_unreadable_history_refuses_preview_and_reviewed_write(self):
        self.reviewed_plan()
        history = self.docs / "history"
        history.mkdir()
        (history / "OLD.md").write_text("LG-0099 is permanently reserved.\n")
        history.chmod(0)
        try:
            try:
                list(history.iterdir())
            except PermissionError:
                pass
            else:
                self.skipTest("runtime can enumerate mode-000 directories")
            self.refused()
        finally:
            history.chmod(0o700)

    def test_symlinked_history_refuses_preview_and_reviewed_write(self):
        self.reviewed_plan()
        history = self.root / "old-history"
        history.mkdir()
        (history / "OLD.md").write_text("LG-0099 is permanently reserved.\n")
        (self.docs / "history").symlink_to(history, target_is_directory=True)
        self.refused()

    def test_symlinked_file_refuses_preview_and_reviewed_write(self):
        self.reviewed_plan()
        history = self.root / "OLD.md"
        history.write_text("LG-0099 is permanently reserved.\n")
        (self.docs / "OLD.md").symlink_to(history)
        self.refused()

    def test_readable_nested_history_reserves_its_ids(self):
        history = self.docs / "history"
        history.mkdir()
        (history / "OLD.md").write_text("LG-0099 is permanently reserved.\n")
        self.reviewed_plan()
        plan = json.loads(self.plan.read_text())
        self.assertEqual(plan["mappings"][0]["id"], "LG-0100")
        result = self.cli("--write")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("| LG-0100 |", (self.docs / "LEDGER.md").read_text())

    def root_layout(self):
        for path in self.docs.iterdir():
            path.rename(self.root / path.name)
        self.docs.rmdir()
        self.docs = self.root

    def test_node_bin_file_link_does_not_block_reservations(self):
        binary = self.docs / "node_modules/.bin/tool"
        binary.parent.mkdir(parents=True)
        target = self.root / "tool.js"
        target.write_text("executable\n")
        binary.symlink_to(target)
        self.reviewed_plan()

    def test_venv_python_file_link_does_not_block_reservations(self):
        binary = self.docs / "venv/bin/python"
        binary.parent.mkdir(parents=True)
        binary.symlink_to(sys.executable)
        self.reviewed_plan()

    def test_non_markdown_fifo_does_not_block_reservations(self):
        os.mkfifo(self.docs / "events")
        self.reviewed_plan()

    def test_root_layout_keeps_nested_worktree_reservations(self):
        self.root_layout()
        binary = self.root / "node_modules/.bin/tool"
        binary.parent.mkdir(parents=True)
        binary.symlink_to(sys.executable)
        history = self.root / ".worktrees/candidate/docs"
        history.mkdir(parents=True)
        (history / "OLD.md").write_text("LG-0099 is permanently reserved.\n")
        self.reviewed_plan()
        plan = json.loads(self.plan.read_text())
        self.assertEqual(plan["mappings"][0]["id"], "LG-0100")

    def test_markdown_fifo_still_refuses(self):
        os.mkfifo(self.docs / "OLD.md")
        self.refused()


if __name__ == "__main__":
    unittest.main()
