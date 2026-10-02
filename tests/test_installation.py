"""Template-derived four-document installation, not an agent-use observation.

The fixture applies Install to a stated cold-start context. System temporary
directories provide a real exit-0 control without an ancestor register.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from tests.test_doctor import install_wiring_block


ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-09-11"
DOCUMENTS = {"README.md", "STATUS.md", "CHANGELOG.md", "DECISIONS.md"}
PROJECT = "Pebble CSV"


class MinimalInstallTests(unittest.TestCase):
    """A new local CSV tool, no plan/terms/brand/specs/findings to seed yet.

    Installation was requested directly, without deliberating an alternative.
    That context warrants a CHANGELOG entry and no adoption decision.
    """

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="minimal-docs-install-")
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name).resolve()
        self.docs = self.project / "docs"
        self.docs.mkdir()
        for name in DOCUMENTS:
            source = (ROOT / "templates" / name).read_text(encoding="utf-8")
            (self.docs / name).write_text(source.replace("YYYY-MM-DD", TODAY), encoding="utf-8")

        # Replace the template's explicit personalization slots, not a canned
        # healthy README. Optional index rows follow their deletion instruction;
        # the index check below catches an optional row missing that instruction.
        readme = self.read("README.md")
        replacements = {
            "[PROJECT NAME]": PROJECT,
            "[One or two sentences on what the project is and its current phase. "
            "Keep it to what a reader needs in order to orient — not marketing.]":
                "Pebble CSV is a local command-line CSV validation tool. "
                "Its first task is to define a single-file input contract.",
            "[who re-reads these docs most often — default: the owner + future agent sessions]":
                "the project owner and future Codex sessions",
            "[Any occasional reviewers noted here.]": "No additional reviewers are expected.",
            "[Populate with project-specific tone. Example default: positive framing, factual, "
            "analytical. Avoid inherently negative words when a neutral alternative works.]":
                "Use direct, factual language about CSV inputs and validation errors.",
            '[Populate — e.g., "prose over bullets unless structure genuinely earns its place. '
            'Tables are fine for genuinely table-shaped data."]':
                "Prefer short paragraphs; use tables when comparing input cases.",
            "[Populate — who is the decider? Default: the project owner.]":
                "The project owner decides scope and user-facing behavior.",
        }
        for old, new in replacements.items():
            self.assertIn(old, readme, "README personalization slot changed")
            readme = readme.replace(old, new)
        readme = "\n".join(line for line in readme.splitlines()
                           if "[Delete this line if not installed.]" not in line) + "\n"
        self.write("README.md", readme)

        status = self.read("STATUS.md").replace("# STATUS", "# STATUS — " + PROJECT, 1)
        status = status.replace("**[Phase name — e.g., Phase 1 — Alignment]**", "**Initial scoping**")
        status = status.replace(
            "[One paragraph on what this phase is producing and its scope boundaries. "
            "Keep to 2–4 sentences, present tense.]",
            "Define the CSV input contract for a local command-line tool. "
            "The current scope covers one input file and no network services.")
        status = status.replace(
            "[The ordered queue of work not yet started — one line each. "
            "What the next session picks up first.]",
            "1. Define the command-line input contract for one CSV file.")
        rows = []
        for line in status.splitlines():
            if line.startswith(("| |", "1. **[one-line question", "*Choices gated on the owner.")):
                continue
            if line.startswith("*No items.* [Or a table:"):
                line = "*No items.*"
            rows.append(line)
        self.write("STATUS.md", "\n".join(rows) + "\n")

        changelog = self.read("CHANGELOG.md").partition("Installed the project-docs-protocol at")[0]
        self.write("CHANGELOG.md", changelog +
                   "Installed the project-docs-protocol at `docs/` and wired `AGENTS.md` "
                   "for Codex. Seeded STATUS for a true cold start with the next input-contract "
                   "task and no in-flight work. ROADMAP and GLOSSARY await a concrete plan or "
                   "project terms; BRAND, specs and a findings ledger are not needed.\n")
        # DECISIONS remains the empty template. Do not invent an adoption entry.
        (self.project / "AGENTS.md").write_text(
            "# " + PROJECT + "\n\n" + install_wiring_block("docs"), encoding="utf-8")

    def read(self, name):
        return (self.docs / name).read_text(encoding="utf-8")

    def write(self, name, text):
        (self.docs / name).write_text(text, encoding="utf-8")

    def test_four_document_readme_indexes_only_installed_files(self):
        self.assertEqual({path.name for path in self.docs.iterdir()}, DOCUMENTS)
        self.assertEqual({path.name for path in self.project.iterdir()}, {"docs", "AGENTS.md"})
        readme = self.read("README.md")
        index = readme.split("## File index", 1)[1].split("\n---", 1)[0]
        indexed = set(re.findall(r"`([A-Z_\-]+\.md)`", index))
        self.assertEqual(indexed, DOCUMENTS, "The README advertises omitted optional files")
        # Check real Markdown links too if the template gains them in future.
        for target in re.findall(r"\]\(([^)]+)\)", readme):
            if "://" not in target and not target.startswith("#"):
                self.assertTrue((self.docs / target.split("#", 1)[0]).exists(), target)

    def test_personalized_minimum_has_empty_decisions_and_doctor_exit_zero(self):
        readme, status = self.read("README.md"), self.read("STATUS.md")
        self.assertIn(PROJECT, readme)
        self.assertIn(PROJECT, status)
        self.assertIn("**Primary reader:** the project owner and future Codex sessions", readme)
        self.assertIn("Use direct, factual language about CSV inputs", readme)
        self.assertIn("**Initial scoping**", status)
        self.assertIn("1. Define the command-line input contract", status)
        # Entry-format examples remain legitimate examples; personal fields and
        # unused STATUS questions must be gone even where Doctor does not look.
        unfenced_readme = re.sub(r"```[^\n]*\n.*?```", "", readme, flags=re.S)
        self.assertNotRegex(unfenced_readme, r"\[[^\]\n]+\]")
        self.assertNotRegex(status, r"\[[^\]\n]+\]")
        self.assertNotIn("YYYY-MM-DD", "".join(self.read(name) for name in DOCUMENTS))
        decisions = self.read("DECISIONS.md")
        self.assertNotRegex(decisions, r"(?m)^##+ ")
        self.assertIn("No decisions logged yet", decisions)
        self.assertNotIn("D-NNNN", decisions)
        self.assertNotIn("[POPULATE", decisions)
        self.assertRegex(readme, r"(?m)^\*Installed via the `project-docs-protocol` skill\.")
        self.assertIn("## " + TODAY + " — initialized project documentation system",
                      self.read("CHANGELOG.md"))
        self.assertIn("Seeded STATUS for a true cold start", self.read("CHANGELOG.md"))
        self.assertNotIn("[One sentence", self.read("CHANGELOG.md"))
        self.assertFalse((self.docs / "BRAND.md").exists())

        before = {p.relative_to(self.project): p.read_bytes()
                  for p in self.project.rglob("*") if p.is_file()}
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts/docs-doctor.py"), str(self.project),
             "--today", TODAY, "--no-git"], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotRegex(result.stdout, r"(?m)^(WARN|FAIL)\s")
        for name in ("wiring-block", "wiring-clauses", "wiring-path", "readme-footer"):
            self.assertRegex(result.stdout, r"(?m)^PASS\s+" + name + r"\s")
        self.assertEqual(before, {p.relative_to(self.project): p.read_bytes()
                                  for p in self.project.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
