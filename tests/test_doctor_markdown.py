"""CLI coverage for list-relative wiring, with a retained development oracle.

The suite needs only the standard library. markdown-it-py was used separately
to check these authored cases; see fixtures/markdown-oracle/README.md.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from tests.test_doctor import ROOT, TODAY, indented, install_wiring_block, seed_register


DOCTOR = Path(os.environ.get("DOCS_DOCTOR_UNDER_TEST", ROOT / "scripts/docs-doctor.py"))


def markdown_cases():
    """Complete shipped Install block, wrapped in independently checked syntax."""
    block = install_wiring_block("docs")
    tight = [line for line in block.splitlines() if line.strip()]
    cases = []

    def add(name, source, live):
        cases.append({"name": name, "source": source, "live": live})

    for marker in ("-", "+", "*"):
        add("nested-bullet-" + {"-": "dash", "+": "plus", "*": "star"}[marker],
            f"{marker} Outer section\n    {marker} Protocol section\n\n" + indented(block, 6), True)
    add("nested-numbered", "1. Outer section\n\n   2. Protocol section\n\n" + indented(block, 6), True)
    add("nested-wide-numbered", "10. Outer section\n\n    20. Protocol section\n\n" + indented(block, 8), True)
    add("ordered-sibling-indentation-code", "1. Outer\n  2. Inner\n\n" + indented(block, 4), False)
    add("ordered-sibling-indentation-live", "1. Outer\n  2. Inner\n\n" + indented(block, 7), True)
    add("wide-numbered-cannot-interrupt-paragraph", "10. Outer section\n    20. Protocol section\n\n" +
        indented(block, 8), False)
    add("nested-tab-padding", "-\tOuter section\n\t-\tProtocol section\n\n" +
        "\n".join("\t\t" + line if line.strip() else "" for line in block.splitlines()) + "\n", True)
    add("bullet-continuation", "- Protocol section\n\n" + indented(block, 4), True)
    add("numbered-continuation", "1. Protocol section\n\n" + indented(block, 6), True)
    add("nested-with-extra-blank", "- Outer section\n\n    - Protocol section\n\n\n" + indented(block, 6), True)
    add("nested-tight-heading", "- Outer section\n    - Protocol section\n" + indented(block, 6), True)
    add("top-level-four-space-code", "Example only:\n\n" + indented(block, 4), False)
    add("top-level-tab-code", "Example only:\n\n" +
        "\n".join("\t" + line if line.strip() else "" for line in block.splitlines()) + "\n", False)
    add("bullet-marker-surplus-tight", "-     " + tight[0] + "\n" + indented("\n".join(tight[1:]), 6), False)
    add("bullet-marker-surplus-blank", "-     " + block.splitlines()[0] + "\n\n" +
        indented("\n".join(block.splitlines()[1:]), 6), False)
    add("numbered-marker-surplus-tight", "1.     " + tight[0] + "\n" + indented("\n".join(tight[1:]), 7), False)
    add("nested-marker-surplus-tight", "- Outer section\n    -     " + tight[0] + "\n" +
        indented("\n".join(tight[1:]), 10), False)
    add("code-after-nested-paragraph", "- Outer section\n    - Protocol section\n\n" + indented(block, 10), False)
    add("nested-fenced-example", "- Outer section\n    - Protocol section\n\n      ```markdown\n" +
        indented(block, 6) + "      ```\n", False)
    # Two list containers and a fence may open on one physical line. The
    # complete authentic wiring block must remain quoted in this form.
    nested_same_line = "- - ```markdown\n" + indented(block, 4) + "    ```\n"
    add("same-line-nested-fenced-authentic", nested_same_line, False)
    # The same containers with an unfenced block stay visible.
    visible_same_line = ("- - ## Project docs protocol\n"
                         "    This project uses the project-docs-protocol (docs in `docs/`).\n"
                         "    - **Session start:** read STATUS in full if it is under ~60 lines.\n"
                         "    - STATUS is rewritten, not appended.\n"
                         "    - **Precedence.** Append CHANGELOG first, edit LEDGER, then rewrite STATUS.\n")
    add("same-line-nested-visible-authentic", visible_same_line, True)
    # A mixed list marker transition ends the preceding bullet container;
    # the five-column fenced block is therefore a quoted example.
    mixed_fenced = "- Parent\n2. - ```markdown\n" + indented(block, 5) + "     ```\n"
    add("mixed-list-transition-fenced-authentic", mixed_fenced, False)
    mixed_active = ("- Parent\n2. - ## Project docs protocol\n"
                    "     This project uses the project-docs-protocol (docs in `docs/`).\n"
                    "     - Read STATUS in full if it is under ~60 lines.\n"
                    "     - STATUS is rewritten, not appended.\n"
                    "     - **Precedence.** CHANGELOG first, edit LEDGER, then rewrite STATUS.\n")
    add("mixed-list-transition-active-positive", mixed_active, True)
    # An empty item is terminated by the blank line; the following six-column
    # fenced block is top-level indented code and must stay hidden.
    empty_item_fenced = "-\n\n    - - ```markdown\n" + indented(block, 6) + "      ```\n"
    add("empty-item-blank-fenced-authentic", empty_item_fenced, False)
    empty_item_active = ("- Parent\n\n    - - ## Project docs protocol\n"
                         "      This project uses the project-docs-protocol (docs in `docs/`).\n"
                         "      - Read STATUS in full if it is under ~60 lines.\n"
                         "      - STATUS is rewritten, not appended.\n"
                         "      - **Precedence.** CHANGELOG first, edit LEDGER, then rewrite STATUS.\n")
    add("empty-item-blank-active-positive", empty_item_active, True)
    add("lazy-top-level-paragraph", "These are active instructions:\n" + indented("\n".join(tight), 4), True)
    add("lazy-nested-paragraph", "- Outer section\n    - These are active instructions:\n" +
        indented("\n".join(tight), 10), True)
    return cases


class DoctorMarkdownTests(unittest.TestCase):
    def setUp(self):
        temporary = ROOT / "tests/.tmp"
        temporary.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="markdown-cli-", dir=temporary)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        seed_register(self.project)

    def check_case(self, case):
        (self.project / "AGENTS.md").write_text(case["source"], encoding="utf-8")
        before = {p.relative_to(self.project): p.read_bytes()
                  for p in self.project.rglob("*") if p.is_file()}
        process = subprocess.run([sys.executable, "-B", str(DOCTOR), str(self.project),
                                  "--today", TODAY, "--no-git"],
                                 capture_output=True, text=True, timeout=15)
        message = process.stdout + process.stderr
        self.assertNotIn("Traceback", message)
        self.assertNotIn("checker error:", message)
        self.assertEqual(process.stderr, "", message)
        checks = dict((name, level) for level, name in
                      re.findall(r"^(PASS|WARN|FAIL|INFO|SKIP)\s+(\S+)", process.stdout, re.M))
        self.assertIn("git-status-churn", checks, message)
        self.assertEqual(checks["nested-register"], "WARN", message)
        expected = ("PASS", "PASS", "PASS") if case["live"] else ("FAIL", "SKIP", "SKIP")
        self.assertEqual(tuple(checks.get(name) for name in
                               ("wiring-block", "wiring-clauses", "wiring-path")), expected, message)
        self.assertEqual(process.returncode, 1 if case["live"] else 2, message)
        self.assertEqual(before, {p.relative_to(self.project): p.read_bytes()
                                  for p in self.project.rglob("*") if p.is_file()},
                         "Doctor modified its input project")

    def test_complete_install_blocks_in_list_containers(self):
        for case in markdown_cases():
            if case["live"] and not case["name"].startswith("lazy-"):
                with self.subTest(case=case["name"]):
                    self.check_case(case)

    def test_code_examples_never_supply_wiring(self):
        for case in markdown_cases():
            if not case["live"]:
                with self.subTest(case=case["name"]):
                    self.check_case(case)

    def test_lazy_paragraph_continuations_remain_live(self):
        for case in markdown_cases():
            if case["name"].startswith("lazy-"):
                with self.subTest(case=case["name"]):
                    self.check_case(case)

    def test_marker_line_sentence_surplus_is_hidden(self):
        source = ("-     This project uses the project-docs-protocol (docs in `docs/`).\n"
                  + indented("- STATUS is rewritten, not appended.\n"
                             "- **Precedence.** CHANGELOG first, then STATUS.\n", 4))
        (self.project / "AGENTS.md").write_text(source, encoding="utf-8")
        process = subprocess.run([sys.executable, "-B", str(DOCTOR), str(self.project),
                                  "--today", TODAY, "--no-git"], capture_output=True, text=True)
        checks = dict((name, level) for level, name in
                      re.findall(r"^(PASS|WARN|FAIL|INFO|SKIP)\s+(\S+)", process.stdout, re.M))
        self.assertEqual(checks.get("wiring-block"), "WARN")
        self.assertNotIn("PASS  wiring-block", process.stdout)

    def test_retained_oracle_covers_current_case_text_and_expectations(self):
        fixture = ROOT / "tests/fixtures/markdown-oracle"
        saved = json.loads((fixture / "observations.json").read_text())
        routing = json.loads((fixture / "observations-routing-20260922.json").read_text())
        # The routing bullet left the Install block (D-0020), so the current
        # inputs are again exactly the text observations.json was recorded on.
        # The 2026-09-22 recording stays as history with the same expectations.
        self.assertEqual([(c['name'], c['live']) for c in routing['cases']],
                         [(c['name'], c['live']) for c in saved['cases']])
        expected = [{key: case[key] for key in ("name", "source", "live")} for case in markdown_cases()]
        self.assertEqual([{key: case[key] for key in ("name", "source", "live")}
                          for case in saved["cases"]], expected)
        self.assertEqual(saved["parser"], "markdown-it-py 4.0.0; commonmark preset")
        for case in saved["cases"]:
            self.assertEqual(case["oracle_live"], case["live"], case["name"])


if __name__ == "__main__":
    unittest.main()
