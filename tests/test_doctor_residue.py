"""Doctor: a symlinked docs/ keeps its selected label, and template residue is caught.

Each generated project stays within tests/.tmp/, like test_doctor.py.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from tests.test_doctor import DOCTOR, ROOT, TODAY, WIRING, load_doctor, seed_register

TEMPLATES = ROOT / "templates"


def template_placeholders(name):
    """Every bracketed span the template ships, except Markdown links."""
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    return re.findall(r"\[[^\[\]\n]+\](?!\()", text)


class ProjectCase(unittest.TestCase):
    def setUp(self):
        temporary = ROOT / "tests/.tmp"
        temporary.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="doctor-", dir=temporary)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        seed_register(self.project)

    def doctor(self):
        process = subprocess.run([sys.executable, "-B", str(DOCTOR), str(self.project),
                                  "--today", TODAY, "--no-git"],
                                 capture_output=True, text=True, timeout=30)
        self.assertNotIn("Traceback", process.stderr, process.stderr)
        levels = dict((name, level) for level, name in
                      re.findall(r"^(PASS|WARN|FAIL|INFO|SKIP)\s+(\S+)", process.stdout, re.M))
        return process.returncode, levels, process.stdout


class SymlinkedDocsTests(ProjectCase):
    def link_docs(self):
        (self.project / "docs").rename(self.project / "realdocs")
        (self.project / "docs").symlink_to("realdocs")

    def test_symlinked_docs_is_labelled_as_selected(self):
        self.link_docs()
        code, levels, out = self.doctor()
        self.assertEqual(levels.get("wiring-path"), "PASS", out)
        self.assertNotIn("register found at realdocs/", out)
        self.assertNotEqual(code, 2, out)

    def test_symlinked_docs_still_fails_a_wrong_declared_path(self):
        self.link_docs()
        (self.project / "AGENTS.md").write_text(WIRING.replace("docs/", "wrong/"), encoding="utf-8")
        code, levels, out = self.doctor()
        self.assertEqual(levels.get("wiring-path"), "FAIL", out)
        self.assertEqual(code, 2, out)

    def test_plain_docs_label_is_unchanged(self):
        code, levels, out = self.doctor()
        self.assertEqual(levels.get("wiring-path"), "PASS", out)
        self.assertIn("register found at docs/", out)


class TemplateResidueTests(ProjectCase):
    def status_with(self, line):
        (self.project / "docs/STATUS.md").write_text(
            "# STATUS\n\nLast updated: %s\n\n## Current phase\n\n%s\n" % (TODAY, line), encoding="utf-8")

    def test_template_ships_placeholders(self):
        self.assertGreaterEqual(len(template_placeholders("STATUS.md")), 6)

    def test_every_status_template_placeholder_is_residue(self):
        regex = load_doctor().STATUS_PLACEHOLDER_RE
        for span in template_placeholders("STATUS.md"):
            with self.subTest(span=span[:40]):
                self.assertTrue(regex.search(span), span)

    def test_unfilled_status_template_warns(self):
        (self.project / "docs/STATUS.md").write_text(
            (TEMPLATES / "STATUS.md").read_text(encoding="utf-8").replace("YYYY-MM-DD", TODAY, 1),
            encoding="utf-8")
        code, levels, out = self.doctor()
        self.assertEqual(levels.get("status-template-residue"), "WARN", out)

    def test_phase_name_and_paragraph_placeholders_warn(self):
        self.status_with("**[Phase name — e.g., Phase 1 — Alignment]**\n\n"
                         "[One paragraph on what this phase is producing and its scope boundaries.]")
        code, levels, out = self.doctor()
        self.assertEqual(levels.get("status-template-residue"), "WARN", out)

    def test_this_repository_status_has_no_residue(self):
        regex = load_doctor().STATUS_PLACEHOLDER_RE
        text = (ROOT / "docs/STATUS.md").read_text(encoding="utf-8")
        self.assertEqual([l for l in text.splitlines() if regex.search(l)], [])

    def test_ordinary_brackets_are_not_residue(self):
        self.status_with("See [the plan](docs/plan.md) and [x] done; array [1, 2].")
        code, levels, out = self.doctor()
        self.assertEqual(levels.get("status-template-residue"), "PASS", out)


class ReadmeResidueTests(ProjectCase):
    def readme(self, title):
        (self.project / "docs/README.md").write_text(
            "%s\n\n*Installed via the `project-docs-protocol` skill.*\n" % title, encoding="utf-8")

    def test_template_title_is_the_residue(self):
        title = (TEMPLATES / "README.md").read_text(encoding="utf-8").splitlines()[0]
        self.assertIn("[PROJECT NAME]", title)
        self.readme(title)
        code, levels, out = self.doctor()
        self.assertEqual(levels.get("readme-footer"), "WARN", out)
        self.assertIn("template placeholder", out)

    def test_real_title_with_footer_passes(self):
        self.readme("# Fixture — Project Docs")
        code, levels, out = self.doctor()
        self.assertEqual(levels.get("readme-footer"), "PASS", out)

    def test_placeholder_title_inside_a_fence_is_ignored(self):
        (self.project / "docs/README.md").write_text(
            "# Fixture\n\n```\n# [PROJECT NAME] — Project Docs\n```\n\n"
            "*Installed via the `project-docs-protocol` skill.*\n", encoding="utf-8")
        code, levels, out = self.doctor()
        self.assertEqual(levels.get("readme-footer"), "PASS", out)


if __name__ == "__main__":
    unittest.main()
