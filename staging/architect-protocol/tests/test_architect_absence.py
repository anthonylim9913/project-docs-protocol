"""Only an omitted default packet under a usable project may be skipped."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/architect-doctor.py"


class ArchitectAbsenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def cli(self, root, *arguments):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), str(root), *arguments],
                              capture_output=True, text=True, timeout=10)

    def assert_failure(self, root, *arguments):
        result = self.cli(root, *arguments)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL architect:", result.stdout)
        self.assertNotIn("SKIP", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_missing_project_root_fails(self):
        target = self.root / "missing/project"
        result = self.assert_failure(target)
        self.assertIn("project root must exist", result.stdout)
        self.assertIn(str(target), result.stdout)

    def test_file_project_root_fails(self):
        target = self.root / "file"
        target.write_text("not a project")
        self.assert_failure(target)

    def test_dangling_project_root_fails(self):
        target = self.root / "link"
        target.symlink_to("missing")
        self.assert_failure(target)

    def test_explicit_missing_packet_fails_even_when_it_names_the_default(self):
        for packet in ("custom/packet", "docs/architect"):
            with self.subTest(packet=packet):
                result = self.assert_failure(self.root, "--packet-dir", packet)
                self.assertIn("explicit packet directory must exist", result.stdout)
                self.assertIn(packet, result.stdout)

    def test_default_absence_skips_with_or_without_docs_directory(self):
        for docs_present in (False, True):
            with self.subTest(docs_present=docs_present):
                if docs_present:
                    (self.root / "docs").mkdir()
                result = self.cli(self.root)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("SKIP architect: packet absent", result.stdout)


if __name__ == "__main__":
    unittest.main()
