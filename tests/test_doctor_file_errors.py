"""Present optional inputs must not disable structural checks silently."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_doctor import BANNER, row, seed_register


DOCTOR = Path(__file__).resolve().parents[1] / "scripts/docs-doctor.py"


class DoctorFileErrorsTests(unittest.TestCase):
    def test_unreadable_decisions_emits_exactly_one_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            seed_register(project)
            target = project / "docs/DECISIONS.md"
            target.chmod(0)
            try:
                try:
                    target.read_bytes()
                except PermissionError:
                    pass
                else:
                    self.skipTest("runtime can read mode-000 files")
                result = subprocess.run(
                    [sys.executable, "-B", str(DOCTOR), str(project),
                     "--today", "2026-09-10", "--no-git"],
                    capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                failures = [line for line in result.stdout.splitlines()
                            if line.startswith("FAIL") and "decisions-ids" in line]
                self.assertEqual(len(failures), 1, result.stdout)
                self.assertIn("unusable", failures[0])
            finally:
                target.chmod(0o600)

    def test_unusable_optional_files_fail_instead_of_appearing_absent(self):
        for name, check in (("docs/LEDGER.md", "ledger"),
                            ("docs/LEDGER-ARCHIVE.md", "ledger-archive-ids"),
                            ("docs/BRAND.md", "brand-placeholders"),
                            ("CLAUDE.md", "wiring-block"),
                            ("docs/README.md", "readme-footer")):
            for kind in ("unreadable", "dangling", "directory", "fifo"):
                with self.subTest(name=name, kind=kind), tempfile.TemporaryDirectory() as temporary:
                    project = Path(temporary)
                    seed_register(project)
                    (project / "docs/LEDGER.md").write_text(BANNER + row())
                    target = project / name
                    target.unlink(missing_ok=True)
                    if kind == "unreadable":
                        target.write_text("reserved input\n")
                        target.chmod(0)
                        try:
                            target.read_bytes()
                        except PermissionError:
                            pass
                        else:
                            self.skipTest("runtime can read mode-000 files")
                    elif kind == "dangling":
                        target.symlink_to("missing-target")
                    elif kind == "directory":
                        target.mkdir()
                    else:
                        os.mkfifo(target)
                    try:
                        result = subprocess.run(
                            [sys.executable, "-B", str(DOCTOR), str(project),
                             "--today", "2026-09-10", "--no-git", "--json"],
                            capture_output=True, text=True, timeout=10)
                        report = json.loads(result.stdout)
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        failures = [entry for entry in report["checks"]
                                    if entry["id"] == check and entry["level"] == "FAIL"]
                        self.assertTrue(failures, report)
                        self.assertIn(target.name, failures[0]["message"])
                        self.assertIn("unusable", failures[0]["message"])
                    finally:
                        if kind == "unreadable":
                            target.chmod(0o600)

    def test_absent_optional_files_keep_their_existing_levels(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            seed_register(project)
            result = subprocess.run(
                [sys.executable, "-B", str(DOCTOR), str(project),
                 "--today", "2026-09-10", "--no-git", "--json"],
                capture_output=True, text=True, timeout=10)
            report = json.loads(result.stdout)
            checks = {entry["id"]: entry["level"] for entry in report["checks"]}
            self.assertEqual(checks["ledger"], "SKIP")
            self.assertEqual(checks["brand-placeholders"], "INFO")
            self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
