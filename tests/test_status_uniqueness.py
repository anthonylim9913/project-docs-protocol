"""Doctor CLI checks for ambiguous dashboards, using handwritten Markdown."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from tests.test_doctor import DOCTOR, TODAY, seed_register


class StatusUniquenessTests(unittest.TestCase):
    def check(self, text, expected=0):
        with tempfile.TemporaryDirectory(prefix="docs-status-uniqueness-") as name:
            project = Path(name)
            seed_register(project)
            (project / "docs/STATUS.md").write_text(text, encoding="utf-8")
            before = {p.relative_to(project): p.read_bytes()
                      for p in project.rglob("*") if p.is_file()}
            result = subprocess.run(
                [sys.executable, "-B", str(DOCTOR), str(project),
                 "--today", TODAY, "--no-git"],
                capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertEqual(before, {p.relative_to(project): p.read_bytes()
                                     for p in project.rglob("*") if p.is_file()})
            return result.stdout

    def test_repeated_canonical_siblings_report_original_line_numbers(self):
        for title in ("Current phase", "In flight", "Blocked", "Deferred",
                      "Next", "Open questions (owner)"):
            with self.subTest(title=title):
                output = self.check(
                    f"# STATUS\n\nLast updated: {TODAY}\n\n"
                    f"## {title}\n\nWait.\n\n   ## **{title.upper()}** ##\n", 1)
                diagnostic = re.search(r"^WARN\s+status-headings\s+(.+)$", output, re.M)
                self.assertIsNotNone(diagnostic, output)
                self.assertIn("lines 5, 9", diagnostic.group(1))

    def test_hidden_examples_do_not_duplicate_live_dashboard_fields(self):
        for hidden in ("```md\n## Next\nLast updated: 2020-01-01\n```",
                       "~~~\n## Next\nLast updated: 2020-01-01\n~~~",
                       "<!--\n## Next\nLast updated: 2020-01-01\n-->",
                       "> ## Next\n> Last updated: 2020-01-01",
                       "    ## Next\n    Last updated: 2020-01-01"):
            with self.subTest(hidden=hidden):
                self.check(f"# STATUS\n\n*Last updated: {TODAY}*\n\n## Next\n\n{hidden}\n")

    def test_lazy_quoted_timestamp_is_not_a_live_field(self):
        for quote in ("> Old example:", "> > Old example:", "> - Old example:"):
            with self.subTest(quote=quote):
                self.check(f"# STATUS\n\nLast updated: {TODAY}\n\n"
                           f"{quote}\nLast updated: 2020-01-01\n")
        for continuation in ("-not a marker", "2. not an interrupting marker"):
            with self.subTest(continuation=continuation):
                self.check(f"# STATUS\n\nLast updated: {TODAY}\n\n"
                           f"> Old example:\n{continuation}\nLast updated: 2020-01-01\n")
        for marker in ("-", "1.", "- -"):
            with self.subTest(list_quote=marker):
                self.check(f"# STATUS\n\nLast updated: {TODAY}\n\n"
                           f"{marker} > Old example:\n"
                           f"{' ' * (len(marker) + 1)}Last updated: 2020-01-01\n")
        for boundary in ("\n", "## Current phase\n", "---\n",
                         "<!-- hidden -->\n", "```\nexample\n```\n"):
            with self.subTest(boundary=boundary):
                self.check(f"# STATUS\n\n> Old example:\n{boundary}"
                           f"Last updated: {TODAY}\n")
        for quote in ("> ## Old example", "> ---", ">", ">     code",
                      "> ```\n> example\n> ```", "> ```\n> example",
                      "> Old example\n> ==="):
            with self.subTest(block_quote=quote):
                self.check(f"# STATUS\n\n{quote}\nLast updated: {TODAY}\n")
        self.check(f"# STATUS\n\n> Old example:\n- Last updated: {TODAY}\n")

    def test_different_heading_levels_and_parent_scopes_are_not_duplicates(self):
        self.check(f"# STATUS\n\nLast updated: {TODAY}\n\n"
                   "## Next\n\n### Next\n\n## Module A\n\n### Blocked\n\n"
                   "## Module B\n\n### Blocked\n")

    def test_custom_headings_are_not_forced_into_canonical_schema(self):
        self.check(f"# STATUS\n\nLast updated: {TODAY}\n\n"
                   "## Queue\n\n## Queue\n\n## Next release\n\n## Next review\n")

    def test_level_three_canonical_siblings_are_checked(self):
        output = self.check(f"# STATUS\n\nLast updated: {TODAY}\n\n"
                            "### Next\n\n### Next\n", 1)
        self.assertRegex(output, r"WARN\s+status-headings[^\n]*lines 5, 7")

    def test_dated_historical_sections_are_not_current_dashboards(self):
        self.check(f"# STATUS\n\nLast updated: {TODAY}\n\n## Next\n\n"
                   "## 2020-01-01 example\n\n### Next\n\n### Next\n")

    def test_dated_document_title_does_not_hide_duplicate_current_sections(self):
        output = self.check(f"# Project STATUS — {TODAY}\n\nLast updated: {TODAY}\n\n"
                            "## Next\n\n## Next\n", 1)
        self.assertRegex(output, r"WARN\s+status-headings[^\n]*lines 5, 7")

    def test_multiple_updated_fields_warn_without_selecting_a_date(self):
        for second in ("**Last updated:** 2020-01-01", "_LAST UPDATED_: 2020-01-01",
                       "Last-updated: invalid", "### Last updated: 2020-01-01",
                       "- **Last updated:** 2020-01-01", "1. **Last updated:** 2020-01-01"):
            with self.subTest(second=second):
                output = self.check(f"# STATUS\n\n*Last updated: {TODAY}*\n\n{second}\n", 1)
                self.assertRegex(output, r"WARN\s+status-last-updated[^\n]*lines 3, 5")
                self.assertNotRegex(output, r"(?:PASS|INFO)\s+status-last-updated")
                self.assertNotIn("lag 0 days", output)

    def test_prose_mention_of_updated_field_is_not_another_timestamp(self):
        self.check(f"# STATUS\n\nLast updated: {TODAY}\n\n## Next\n\n"
                   "Check the Last updated field when a blocker changes.\n")

    def test_single_formatted_updated_field_is_usable_but_quote_is_not(self):
        for label in ("**Last-updated:**", "_Last updated_:", "**Last updated:**",
                      "- **Last updated:**", "1. **Last updated:**"):
            with self.subTest(label=label):
                output = self.check(f"# STATUS\n\n{label} {TODAY}\n")
                self.assertRegex(output, r"PASS\s+status-last-updated")
        output = self.check(f"# STATUS\n\n> Last updated: {TODAY}\n", 1)
        self.assertRegex(output, r"WARN\s+status-last-updated[^\n]*no 'Last updated")

    def test_same_date_is_ambiguous_even_if_one_field_is_malformed(self):
        for first in (TODAY, "not a date"):
            with self.subTest(first=first):
                output = self.check(f"# STATUS\n\nLast updated: {first}\n\n"
                                    f"Last updated: {TODAY}\n", 1)
                self.assertRegex(output, r"WARN\s+status-last-updated[^\n]*lines 3, 5")
                self.assertEqual(len(re.findall(r"^(?:PASS|WARN|INFO)\s+status-last-updated\b", output, re.M)), 1)


if __name__ == "__main__":
    unittest.main()
