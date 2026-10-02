"""CLI regressions; each generated project stays within tests/.tmp/.

Two suites deliberately work outside that directory: the git checks need a
real repository of their own, and the fresh-install exercise needs a project
with no register above it so `exit 0` can be asserted literally.
"""
from pathlib import Path
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "scripts/docs-doctor.py"
TODAY = "2026-09-10"
COLUMNS = ("ID", "P", "Status", "Date", "Title", "Tags", "Closes-when",
           "Blocked-on", "Touches", "Evidence")
HEADER = "| " + " | ".join(COLUMNS) + " |\n"
SEPARATOR = "|" + "---|" * len(COLUMNS) + "\n"
BANNER = "# LEDGER\n\nTags: +brief\n\n## Items\n\n" + HEADER + SEPARATOR
WIRING = """## Project docs protocol

This project uses the project-docs-protocol (docs in `docs/`).

- Read STATUS in full if it is under ~60 lines.
- STATUS is rewritten, not appended.
- **Precedence.** Append CHANGELOG first, edit LEDGER, then rewrite STATUS.
"""


def row(**changes):
    values = dict(zip(COLUMNS, ("LG-0001", "P1", "OPEN", TODAY, "finding",
                               "+brief", "check exits 0", "", "src", "origin")))
    values.update(changes)
    return "| " + " | ".join(values[c] for c in COLUMNS) + " |\n"


def load_doctor():
    """Import scripts/docs-doctor.py as a module (its filename is not an
    identifier, so importlib does the loading)."""
    spec = importlib.util.spec_from_file_location("docs_doctor_under_test", DOCTOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def install_wiring_block(docs_path):
    """The exact block Mode 1 Install step 2 tells the installer to paste,
    read out of SKILL.md so the fixture cannot drift away from the document."""
    step = (ROOT / "SKILL.md").read_text(encoding="utf-8").split("### Step 2", 1)[1]
    block = step.split("```markdown", 1)[1].split("```", 1)[0].strip("\n")
    assert "## Project docs protocol" in block, "SKILL.md step 2 block not found"
    return block.replace("<docs-path>", docs_path) + "\n"


def seed_register(project):
    """Write the small healthy register the CLI fixtures share into `project`."""
    docs = project / "docs"
    docs.mkdir(exist_ok=True)
    (project / "AGENTS.md").write_text(WIRING, encoding="utf-8")
    (docs / "README.md").write_text("*Installed via the `project-docs-protocol` skill.*\n", encoding="utf-8")
    (docs / "STATUS.md").write_text(
        f"# STATUS\n\nLast updated: {TODAY}\n\n## Current phase\n\nFixture review.\n", encoding="utf-8")
    (docs / "CHANGELOG.md").write_text(
        f"# CHANGELOG\n\n## {TODAY} — initialized project documentation system\n\nInstalled.\n", encoding="utf-8")
    (docs / "DECISIONS.md").write_text("# DECISIONS\n", encoding="utf-8")


def indented(block, width=4):
    """`block` as a CommonMark indented chunk: every non-blank line pushed
    right by `width` columns. Blank lines stay blank (trailing spaces on a
    blank line would not change anything, and no register writes them)."""
    return "\n".join((" " * width + line if line.strip() else line)
                      for line in block.splitlines()) + "\n"


class DoctorTests(unittest.TestCase):
    def setUp(self):
        temporary = ROOT / "tests/.tmp"
        temporary.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="doctor-", dir=temporary)
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        self.docs = self.project / "docs"
        self.docs.mkdir()
        seed_register(self.project)

    def write(self, path, text):
        (self.project / path).write_text(text, encoding="utf-8")

    def ledger(self, *rows):
        self.write("docs/LEDGER.md", BANNER + "".join(rows))

    def archive(self, *rows):
        self.write("docs/LEDGER-ARCHIVE.md", HEADER + SEPARATOR + "".join(rows))

    def run_doctor(self, expected=0, checks=None, root=None):
        before = {p.relative_to(self.project): p.read_bytes()
                  for p in self.project.rglob("*") if p.is_file()}
        process = subprocess.run([sys.executable, "-B", str(DOCTOR), str(root or self.project),
                                  "--today", TODAY, "--no-git"],
                                 capture_output=True, text=True, timeout=15)
        message = process.stdout[-14000:] + process.stderr
        self.assertNotIn("checker error:", process.stderr, message)
        self.assertNotIn("Traceback", process.stderr, message)
        # The enclosing repository owns a register, so isolated fixtures have
        # an intentional nested-register advisory. This is not masked away.
        self.assertEqual(process.returncode, max(expected, 1), message)
        levels = dict((name, level) for level, name in
                      re.findall(r"^(PASS|WARN|FAIL|INFO|SKIP)\s+(\S+)", process.stdout, re.M))
        if expected != 3:
            self.assertEqual(levels.get("nested-register"), "WARN", message)
            self.assertIn("git-status-churn", levels, "Doctor stopped before later checks\n" + message)
        for check, level in (checks or {}).items():
            self.assertEqual(levels.get(check), level, message)
        if expected == 0:
            self.assertEqual({name for name, level in levels.items() if level in {"FAIL", "WARN"}},
                             {"nested-register"}, message)
        after = {p.relative_to(self.project): p.read_bytes()
                 for p in self.project.rglob("*") if p.is_file()}
        self.assertEqual(before, after, "Doctor modified its input project")
        return process.stdout

    def test_healthy_ledger(self):
        self.ledger(row())
        self.archive()
        self.run_doctor(checks={"ledger-schema": "PASS", "ledger-stale-open": "PASS",
                                "ledger-archive-ids": "PASS"})

    def test_last_updated_field_after_other_text_on_the_line(self):
        # A STATUS that opens with a note and closes the line with the field
        # is current; the field need not start the line.
        self.write("docs/STATUS.md", "# STATUS\n\n*Current-state snapshot; history belongs in "
                   "CHANGELOG. Last updated: %s.*\n\n## Current phase\n\nFixture review.\n" % TODAY)
        self.run_doctor(checks={"status-last-updated": "PASS"})

    def test_last_updated_lag_is_reported_when_the_field_follows_metadata(self):
        # The date is the one after the field, never an earlier date on the line,
        # and a real lag must not be hidden behind "no line found".
        import datetime
        stale = (datetime.date.fromisoformat(TODAY) - datetime.timedelta(days=49)).isoformat()
        self.write("docs/STATUS.md", "# STATUS\n\n**Merged to `main`** (since 2020-01-01) · "
                   "**Last updated:** %s\n\n## Current phase\n\nFixture review.\n" % stale)
        out = self.run_doctor(expected=1, checks={"status-last-updated": "WARN"})
        self.assertIn("49 days behind", out)

    def test_prose_mentioning_last_updated_is_not_a_second_field(self):
        self.write("docs/STATUS.md", "# STATUS\n\nLast updated: %s\n\nNote: the Last updated: line "
                   "is bumped at Close.\n\n## Current phase\n\nFixture review.\n\n## Next\n\n"
                   "1. Remember the close ritual bumps the Last updated: field.\n" % TODAY)
        self.run_doctor(checks={"status-last-updated": "PASS"})

    def test_absent_ledger_has_single_skip(self):
        output = self.run_doctor(checks={"ledger": "SKIP"})
        self.assertEqual(len(re.findall(r"^SKIP\s+ledger\s", output, re.M)), 1)

    def test_missing_root(self):
        self.run_doctor(3, root=self.project / "absent")

    def test_missing_register(self):
        empty = self.project / "empty"
        empty.mkdir()
        self.run_doctor(3, root=empty)

    def test_malformed_ledger_headers_do_not_abort_later_checks(self):
        for content in ("# LEDGER\n", BANNER.replace("| P |", "| Priority |"),
                        BANNER.replace("| P |", "|"), ""):
            with self.subTest(content=content):
                self.write("docs/LEDGER.md", content)
                self.run_doctor(2, {"ledger-header": "FAIL", "ledger-schema": "SKIP",
                                    "ledger-live-size": "SKIP", "decisions-tags": "PASS"})

    def test_bad_row_cell_counts_still_check_well_formed_rows(self):
        self.write("docs/LEDGER.md", BANNER + "| LG-0002 | missing cells |\n" +
                   row(**{"Blocked-on": "owner"}))
        self.run_doctor(2, {"ledger-header": "FAIL", "ledger-schema": "FAIL",
                            "ledger-blocked-on": "FAIL"})

    def test_escaped_pipe_and_unescaped_pipe(self):
        self.ledger(row(Evidence=r"origin \| alternative"))
        self.run_doctor(checks={"ledger-header": "PASS"})
        self.ledger(row(Evidence="origin `a|b`"))
        self.run_doctor(2, {"ledger-header": "FAIL"})

    def test_oversized_primary_id(self):
        self.ledger(row(ID="LG-" + "9" * 5000))
        self.run_doctor(2, {"ledger-ids": "FAIL"})

    def test_oversized_references_in_every_cell(self):
        for column in COLUMNS[1:]:
            with self.subTest(column=column):
                self.ledger(row(**{column: "LG-" + "9" * 5000}))
                self.run_doctor(2, {"ledger-references": "FAIL"})

    def test_oversized_superseded_successor_is_not_valid(self):
        self.ledger(row(Status="SUPERSEDED", Evidence="successor LG-" + "9" * 5000))
        self.run_doctor(2, {"ledger-references": "FAIL", "ledger-schema": "FAIL"})

    def test_oversized_blocked_reference_is_not_valid(self):
        self.ledger(row(Status="BLOCKED", **{"Blocked-on": "LG-" + "9" * 5000}))
        self.run_doctor(2, {"ledger-references": "FAIL", "ledger-blocked-on": "FAIL"})

    def test_numeric_aliases_collide_with_live_ids(self):
        for live, archived in (("LG-1", "LG-0001"), ("LG-0001", "LG-1"),
                               ("UI-LG-001", "UI-LG-1")):
            with self.subTest(live=live, archived=archived):
                self.ledger(row(ID=live))
                self.archive(row(ID=archived, Status="CLOSED"))
                self.run_doctor(2, {"ledger-archive-ids": "FAIL"})

    def test_live_numeric_alias_duplicate(self):
        self.ledger(row(ID="LG-1"), row(ID="LG-0001"))
        self.run_doctor(2, {"ledger-ids": "FAIL"})

    def test_archive_malformed_or_oversized_ids_are_diagnosed(self):
        self.ledger(row())
        for identifier in ("LG-invalid", "LG-" + "9" * 5000, "", "NOT-ID"):
            with self.subTest(identifier=identifier[:24]):
                self.archive(row(ID=identifier, Status="CLOSED"))
                self.run_doctor(2, {"ledger-archive-ids": "FAIL"})

    def test_archive_ids_in_hidden_examples_are_not_reserved(self):
        self.ledger(row())
        hidden = HEADER + SEPARATOR + row(Status="CLOSED")
        self.write("docs/LEDGER-ARCHIVE.md", "```markdown\n" + hidden + "```\n")
        self.run_doctor(checks={"ledger-archive-ids": "PASS"})

    def test_archive_different_prefix_is_distinct(self):
        self.ledger(row())
        self.archive(row(ID="UI-LG-0001", Status="CLOSED"))
        self.run_doctor(checks={"ledger-archive-ids": "PASS"})

    def test_foreign_prefixed_decision_citation_is_reported_not_failed(self):
        # A citation such as RR-D-025 belongs to another register's decision
        # series when this register has no RR-D entries. It is informational;
        # only an unprefixed local D-NNN citation is a missing-entry warning.
        self.write("docs/CHANGELOG.md", f"# CHANGELOG\n\n## {TODAY} — cites RR-D-025\n\nSee RR-D-025.\n")
        output = self.run_doctor(checks={"changelog-decision-refs": "INFO"})
        self.assertIn("not judged", output)

    def test_repeated_archive_closures_remain_valid_history(self):
        self.ledger(row())
        self.archive(row(ID="LG-2", Status="CLOSED", Evidence="first closure"),
                     row(ID="LG-0002", Status="CLOSED", Evidence="second closure after reopen"))
        self.run_doctor(checks={"ledger-archive-ids": "PASS"})

    def test_archive_comments_do_not_create_collisions(self):
        self.ledger(row())
        self.write("docs/LEDGER-ARCHIVE.md", HEADER + SEPARATOR +
                   "<!--\n" + row(Status="CLOSED") + "-->\n")
        self.run_doctor(checks={"ledger-archive-ids": "PASS"})

    def test_maximum_width_ledger_ids_and_references_are_valid(self):
        self.ledger(row(Status="BLOCKED", **{"Blocked-on": "LG-999999999999"}),
                    row(ID="LG-999999999999"))
        self.run_doctor(checks={"ledger-ids": "INFO", "ledger-references": "PASS",
                                "ledger-blocked-on": "PASS"})

    def test_invalid_empty_template_and_future_dates(self):
        for value in ("", "YYYY-MM-DD", "2026-13-45", "2026-02-30", "2027-01-01"):
            with self.subTest(value=value):
                self.ledger(row(Date=value))
                self.run_doctor(1, {"ledger-date": "WARN", "ledger-stale-open": "WARN"})

    def test_deadline_cannot_refresh_staleness(self):
        self.ledger(row(Date="2026-05-01", Evidence="Deadline 2026-09-10; no triage"))
        self.run_doctor(1, {"ledger-date": "PASS", "ledger-stale-open": "WARN"})

    def test_exact_triage_refreshes_staleness(self):
        self.ledger(row(Date="2026-05-01", Evidence="origin; TRIAGE 2026-09-10: still open"))
        self.run_doctor(checks={"ledger-stale-open": "PASS"})

    def test_invalid_future_or_nonexact_triage_cannot_refresh(self):
        for value in ("TRIAGE 2027-01-01: wait", "TRIAGE 2026-13-45: typo", "TRIAGE 2026-09-10 no colon"):
            with self.subTest(value=value):
                self.ledger(row(Date="2026-05-01", Evidence=value))
                self.run_doctor(1, {"ledger-stale-open": "WARN"})

    def test_tombstones_do_not_dilute_stale_live_majority(self):
        rows = [row(ID=f"LG-{n:04}", P="P2", Date="2026-05-01") for n in (1, 2)]
        rows += [row(ID=f"LG-{n:04}", Status="NOT-AN-ISSUE", Title="DO-NOT-RESURRECT ruled out")
                 for n in range(3, 7)]
        self.ledger(*rows)
        self.run_doctor(1, {"ledger-stale-open": "WARN", "ledger-terminal-leak": "PASS"})

    def test_only_not_an_issue_can_be_a_live_terminal_tombstone(self):
        for status in ("CLOSED", "SUPERSEDED"):
            with self.subTest(status=status):
                self.ledger(row(Status=status, Title="DO-NOT-RESURRECT finding"))
                self.run_doctor(2, {"ledger-terminal-leak": "FAIL"})

    def test_nonblocked_owner_gate(self):
        self.ledger(row(**{"Blocked-on": "owner"}))
        self.run_doctor(2, {"ledger-schema": "FAIL", "ledger-blocked-on": "FAIL"})

    def test_blocked_row_requires_gate(self):
        self.ledger(row(Status="BLOCKED"))
        self.run_doctor(2, {"ledger-schema": "FAIL", "ledger-blocked-on": "FAIL"})

    def test_blocked_numeric_alias_resolves(self):
        self.ledger(row(Status="BLOCKED", **{"Blocked-on": "LG-2"}), row(ID="LG-0002"))
        self.run_doctor(checks={"ledger-blocked-on": "PASS"})

    def test_missing_blocker_warns(self):
        self.ledger(row(Status="BLOCKED", **{"Blocked-on": "LG-0002"}))
        self.run_doctor(1, {"ledger-blocked-on": "WARN"})

    def test_superseded_self_reference_is_not_successor(self):
        self.ledger(row(Status="SUPERSEDED", Evidence="successor LG-1"))
        self.run_doctor(2, {"ledger-schema": "FAIL"})

    def test_superseded_distinct_successor_is_structurally_valid(self):
        self.ledger(row(Status="SUPERSEDED", Evidence="successor LG-2"), row(ID="LG-0002"))
        self.run_doctor(2, {"ledger-schema": "PASS", "ledger-terminal-leak": "FAIL"})

    def test_closed_evidence_structure_positive_and_negative(self):
        for evidence, expected in (("done", "FAIL"),
                                   ("src/check.py; command pytest: 4 passed; committed", "PASS"),
                                   ("artifacts/check.json sha256 abc123; command verify: pass", "PASS")):
            with self.subTest(evidence=evidence):
                self.ledger(row(Status="CLOSED", Evidence=evidence))
                self.run_doctor(2, {"ledger-evidence": expected, "ledger-terminal-leak": "FAIL"})

    def test_nested_fences_and_quotes_hide_wiring(self):
        for agents in ("````\n```\n" + WIRING + "```\n````\n",
                       "~~~~\n```\n" + WIRING + "```\n~~~~\n",
                       "\n".join("> " + line for line in WIRING.splitlines())):
            with self.subTest(agents=agents[:30]):
                self.write("AGENTS.md", agents)
                self.run_doctor(2, {"wiring-block": "FAIL"})

    def test_fence_language_info_hides_wiring(self):
        self.write("AGENTS.md", "```markdown\n" + WIRING + "```\n")
        self.run_doctor(2, {"wiring-block": "FAIL"})

    def test_wrong_wiring_path_and_scattered_clauses(self):
        self.write("AGENTS.md", WIRING.replace("docs/", "wrong/"))
        self.run_doctor(2, {"wiring-path": "FAIL"})
        self.write("AGENTS.md", WIRING.replace("- Read STATUS", "## Historical\n\n- Read STATUS"))
        self.run_doctor(1, {"wiring-clauses": "WARN"})

    def test_negated_footer_prefix_and_suffix(self):
        for text in ("Not installed via the `project-docs-protocol` skill.",
                     "Installed via the `project-docs-protocol` skill, but this is not an installation."):
            with self.subTest(text=text):
                self.write("docs/README.md", text + "\n")
                self.run_doctor(1, {"readme-footer": "WARN"})

    def test_indented_headings_and_real_id_with_placeholder_title(self):
        self.write("docs/DECISIONS.md", "# DECISIONS\n\n  ## D-0001 — real title YYYY-MM-DD\n\n  ## D-0001 — repeated\n")
        self.run_doctor(2, {"decisions-ids": "FAIL"})

    def test_deep_decision_heading_is_reported_alongside_normal_heading(self):
        self.write("docs/DECISIONS.md", "# DECISIONS\n\n## D-0001 — first\n\n#### D-0002 — deep\n")
        self.run_doctor(1, {"decisions-id-level": "WARN"})

    def test_commented_status_records_are_ignored(self):
        path = self.docs / "STATUS.md"
        self.write("docs/STATUS.md", "<!--\nLAST SESSION: yesterday\nPRIOR SESSION: before\n-->\n" + path.read_text())
        self.run_doctor(checks={"status-session-stack": "PASS", "status-last-updated": "PASS"})

    def test_future_status_date_warns(self):
        self.write("docs/STATUS.md", "# STATUS\n\nLast updated: 2027-01-01\n")
        self.run_doctor(1, {"status-last-updated": "WARN"})

    def test_decision_reference_holes_and_bodies(self):
        for reference in ("D-0011–D-0013", "D-0011—D-0013", "D-0011 and body D-0012"):
            with self.subTest(reference=reference):
                self.write("docs/CHANGELOG.md", f"# CHANGELOG\n\n## {TODAY} — brief\n\nReserved decisions: {reference}\n")
                self.write("docs/DECISIONS.md", "# DECISIONS\n\n## D-0011 — first\n\n## D-0013 — third\n")
                output = self.run_doctor(1, {"changelog-decision-refs": "WARN"})
                self.assertIn("missing D-0012", output)

    def test_all_decision_range_members_resolve(self):
        self.write("docs/CHANGELOG.md", f"# CHANGELOG\n\n## {TODAY} — brief\n\nReserved decisions: D-0011–D-0013\n")
        self.write("docs/DECISIONS.md", "# DECISIONS\n\n" + "\n".join(f"## D-{n:04} — choice\n" for n in range(11, 14)))
        self.run_doctor(checks={"changelog-decision-refs": "INFO"})

    def test_undeclared_decision_tag_remedy_preserves_history(self):
        self.ledger(row())
        self.write("docs/DECISIONS.md", "# DECISIONS\n\n## D-0001 — choice +unknown\n")
        output = self.run_doctor(2, {"decisions-tags": "FAIL"})
        self.assertNotIn("drop it from the title", output)
        self.assertIn("append a correction", output)

    # --- defect: a CommonMark indented code block is not instructions ------

    def test_indented_code_example_is_not_a_wiring_block(self):
        """Four spaces after a blank line is a code block, so an *example* of
        the wiring block is not the wiring block. Against 88b90b4 this fixture
        printed PASS wiring-block / wiring-clauses / wiring-path and exit 0."""
        self.write("AGENTS.md",
                   "Here is an example of the block you would add:\n\n" + indented(WIRING))
        output = self.run_doctor(2, {"wiring-block": "FAIL", "wiring-clauses": "SKIP",
                                     "wiring-path": "SKIP"})
        self.assertIn("visible, unquoted line", output)

    def test_tab_indented_code_example_is_not_a_wiring_block(self):
        """One tab advances to the same four-column stop as four spaces."""
        self.write("AGENTS.md", "Example only:\n\n" + indented(WIRING).replace("    ", "\t"))
        self.run_doctor(2, {"wiring-block": "FAIL"})

    def test_wiring_indented_inside_a_list_item_is_still_a_block(self):
        """The false positive the rule must not have: content indented under a
        list marker is list content, because the marker moves the content
        baseline. Four spaces under `- ` is two columns of item content, not
        four columns of code."""
        self.write("AGENTS.md", "- Install step 2:\n\n" + indented(WIRING))
        self.run_doctor(checks={"wiring-block": "PASS", "wiring-clauses": "PASS",
                                "wiring-path": "PASS"})

    def test_wiring_indented_inside_a_numbered_item_is_still_a_block(self):
        """`1. ` pushes the baseline to column 3, so even a six-space chunk
        under it is item content."""
        self.write("AGENTS.md", "1. Install step 2:\n\n" + indented(WIRING, 6))
        self.run_doctor(checks={"wiring-block": "PASS", "wiring-clauses": "PASS",
                                "wiring-path": "PASS"})

    def test_same_line_fence_after_root_list_transition_is_hidden(self):
        """A newly opened ordered list may nest a fenced example after a
        preceding bullet; its complete Install block is still quoted code."""
        block = install_wiring_block("docs").strip("\n")
        source = "- Parent\n2. - ```markdown\n" + "".join(
            ("     " + line + "\n") if line.strip() else "\n"
            for line in block.splitlines()) + "     ```\n"
        self.write("AGENTS.md", source)
        self.run_doctor(2, {"wiring-block": "FAIL", "wiring-clauses": "SKIP",
                            "wiring-path": "SKIP"})

    def test_same_line_fence_after_empty_list_transition_is_hidden(self):
        """An empty item followed by a blank line closes before a four-space
        code block, including nested marker text that resembles a fence."""
        block = install_wiring_block("docs").strip("\n")
        source = "-\n\n    - - ```markdown\n" + "".join(
            ("      " + line + "\n") if line.strip() else "\n"
            for line in block.splitlines()) + "      ```\n"
        self.write("AGENTS.md", source)
        self.run_doctor(2, {"wiring-block": "FAIL", "wiring-clauses": "SKIP",
                            "wiring-path": "SKIP"})

    def test_same_line_unfenced_list_transition_remains_live(self):
        """The list transition remains an active block when the fenced
        wrapper is removed, so the visibility repair does not over-hide it."""
        block = install_wiring_block("docs").strip("\n")
        lines = block.splitlines()
        source = "-\n\n- - " + lines[0] + "\n" + "".join(
            ("  " + line + "\n") if line.strip() else "\n"
            for line in lines[1:])
        self.write("AGENTS.md", source)
        self.run_doctor(checks={"wiring-block": "PASS", "wiring-clauses": "PASS",
                                "wiring-path": "PASS"})

    def test_three_space_indent_is_not_code(self):
        self.write("AGENTS.md", "Example only:\n\n" + indented(WIRING, 3))
        self.run_doctor(checks={"wiring-block": "PASS"})

    # --- defect: a separator row with the wrong cell count builds no table --

    def test_ledger_delimiter_cell_count_must_match_the_header(self):
        """GFM builds a table only when the delimiter row has as many cells as
        the header. Against 88b90b4 this fixture printed
        `PASS ledger-header ... 1 rows x 10 cells, 1 table`."""
        self.write("docs/LEDGER.md",
                   "# LEDGER\n\nTags: +brief\n\n## Items\n\n" + HEADER + "|---|---|\n" + row())
        output = self.run_doctor(2, {"ledger-header": "FAIL", "ledger-schema": "SKIP",
                                     "ledger-live-size": "SKIP"})
        self.assertIn("delimiter row has 2 cells, header has 10", output)

    def test_ledger_delimiter_cells_must_be_dashes(self):
        """Separator *shape* is not enough: every cell must match `:?-+:?`."""
        cells = ["---"] * len(COLUMNS)
        cells[3] = ""
        self.write("docs/LEDGER.md",
                   "# LEDGER\n\nTags: +brief\n\n## Items\n\n" + HEADER
                   + "|" + "|".join(cells) + "|\n" + row())
        output = self.run_doctor(2, {"ledger-header": "FAIL"})
        self.assertIn("not dashes with optional alignment colons", output)

    def test_ledger_alignment_colons_remain_a_valid_delimiter(self):
        """The false positive the rule must not have: `:---`, `---:` and
        `:---:` are ordinary GFM alignment markers."""
        cells = [":---", "---:", ":---:"] + ["---"] * (len(COLUMNS) - 3)
        self.write("docs/LEDGER.md",
                   "# LEDGER\n\nTags: +brief\n\n## Items\n\n" + HEADER
                   + "| " + " | ".join(cells) + " |\n" + row())
        self.run_doctor(checks={"ledger-header": "PASS", "ledger-schema": "PASS"})


class VisibleLinesTests(unittest.TestCase):
    """The CommonMark indented-code rule at the level it is implemented.

    A false positive here hides live instructions on a healthy project, which
    is worse than the defect it closes, so every boundary gets its own case.
    """

    doctor = load_doctor()

    def classify(self, text):
        """The 1-based line numbers visible_lines() yields for one document.
        A hidden line is consumed, so it is simply absent."""
        lines = self.doctor.split_lines(text)
        return {index + 1 for index, _, _ in self.doctor.visible_lines(lines)}

    def assertHidden(self, text, *numbers):
        seen = self.classify(text)
        self.assertTrue(seen, "no lines were yielded at all:\n%s" % text)
        for number in numbers:
            self.assertNotIn(number, seen, "line %d should be hidden:\n%s" % (number, text))

    def assertShown(self, text, *numbers):
        seen = self.classify(text)
        self.assertTrue(seen, "no lines were yielded at all:\n%s" % text)
        for number in numbers:
            self.assertIn(number, seen, "line %d should be visible:\n%s" % (number, text))

    def test_chunk_after_a_blank_line_is_code(self):
        self.assertHidden("A paragraph.\n\n    code line\n", 3)

    def test_chunk_at_the_start_of_the_document_is_code(self):
        self.assertHidden("    code line\nstill code? no — this ends it\n", 1)

    def test_a_tab_counts_as_four_columns(self):
        self.assertHidden("A paragraph.\n\n\tcode line\n", 3)

    def test_three_spaces_are_not_code(self):
        self.assertShown("A paragraph.\n\n   not code\n", 3)

    def test_lazy_continuation_of_a_paragraph_is_not_code(self):
        """No blank line above: the indented line continues the paragraph."""
        self.assertShown("A paragraph\n    continues here.\n", 1, 2)

    def test_a_block_ender_above_lets_code_start(self):
        self.assertHidden("## Heading\n    code line\n", 2)
        self.assertHidden("---\n    code line\n", 2)

    def test_content_under_a_bullet_is_list_content(self):
        self.assertShown("- item\n\n    still the item\n", 3)

    def test_content_under_a_numbered_item_is_list_content(self):
        """`1. ` moves the baseline to column 3, so six spaces is still item
        content and only column 7 starts code."""
        self.assertShown("1. item\n\n      still the item\n", 3)
        self.assertHidden("1. item\n\n       code in the item\n", 3)

    def test_eight_spaces_under_a_bullet_is_code_in_the_item(self):
        self.assertHidden("- item\n\n        code in the item\n", 3)

    def test_a_nested_bullet_is_not_code(self):
        self.assertShown("- item\n    - nested item\n", 1, 2)

    def test_baseline_returns_when_the_list_closes(self):
        self.assertShown("- item\n\nA new paragraph.\n", 3)
        self.assertHidden("- item\n\nA new paragraph.\n\n    code line\n", 5)

    def test_a_dash_without_a_space_is_not_a_marker(self):
        self.assertHidden("-notamarker\n\n    code line\n", 3)

    def test_blank_lines_do_not_end_the_block_but_an_outdent_does(self):
        text = "Intro.\n\n    first\n\n    second\nback to prose\n"
        self.assertHidden(text, 3, 5)
        self.assertShown(text, 6)

    def test_a_fence_still_hides_its_body(self):
        self.assertHidden("```\ninside\n```\nafter\n", 2)
        self.assertShown("```\ninside\n```\nafter\n", 4)

    def test_a_comment_body_is_still_dropped_entirely(self):
        self.assertHidden("<!--\nhidden\n-->\nafter\n", 2)
        self.assertShown("<!--\nhidden\n-->\nafter\n", 4)


class DoctorGitTests(unittest.TestCase):
    """The git-backed checks. Every other Doctor fixture forces --no-git, so
    without these the churn and repository lines have no regression cover.
    The repository is built outside the skill repository and its identity comes
    from the environment, so the test never reads the user's git config."""

    def setUp(self):
        if shutil.which("git") is None:
            raise unittest.SkipTest("git is not on PATH")
        self.project = Path(tempfile.mkdtemp(prefix="doctor-git-")).resolve()
        self.addCleanup(shutil.rmtree, self.project)
        self.env = dict(os.environ,
                        GIT_AUTHOR_NAME="Doctor Fixture", GIT_AUTHOR_EMAIL="doctor@example.invalid",
                        GIT_COMMITTER_NAME="Doctor Fixture", GIT_COMMITTER_EMAIL="doctor@example.invalid",
                        GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_TERMINAL_PROMPT="0")
        self.git("init")
        seed_register(self.project)

    def git(self, *args):
        done = subprocess.run(["git", "-C", str(self.project)] + list(args),
                              capture_output=True, text=True, env=self.env, timeout=60)
        self.assertEqual(done.returncode, 0, " ".join(args) + "\n" + done.stdout + done.stderr)
        return done.stdout

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-m", message)

    def status_path(self):
        return self.project / "docs/STATUS.md"

    def write_status(self, body):
        self.status_path().write_text(
            "# STATUS\n\nLast updated: %s\n\n## Current phase\n\n%s\n" % (TODAY, body),
            encoding="utf-8")

    def doctor(self, root=None):
        done = subprocess.run([sys.executable, "-B", str(DOCTOR), str(root or self.project),
                               "--today", TODAY],
                              capture_output=True, text=True, timeout=60)
        self.assertNotIn("checker error:", done.stderr, done.stdout + done.stderr)
        self.assertNotIn("Traceback", done.stderr, done.stdout + done.stderr)
        return done.stdout

    def check_line(self, output, check):
        found = re.search(r"^(PASS|WARN|FAIL|INFO|SKIP)\s+%s\s+(.*)$" % re.escape(check),
                          output, re.M)
        self.assertIsNotNone(found, "no %s line in:\n%s" % (check, output))
        return found.group(1), found.group(2)

    def test_uncommitted_status_cannot_be_measured(self):
        level, text = self.check_line(self.doctor(), "git-status-churn")
        self.assertEqual(level, "SKIP")
        self.assertIn("no commits", text)
        self.assertEqual(self.check_line(self.doctor(), "git-repository")[1],
                         "project root is the repository root")

    def test_too_few_commits_is_informational(self):
        self.commit("install")
        level, text = self.check_line(self.doctor(), "git-status-churn")
        self.assertEqual(level, "INFO")
        self.assertIn("1 commits touching STATUS.md", text)
        self.assertIn("too few to judge churn", text)

    def test_appended_status_history_warns(self):
        """A STATUS that is only ever appended to deletes nothing."""
        self.write_status("Line 1.")
        self.commit("install")
        for n in range(2, 13):
            with self.status_path().open("a", encoding="utf-8") as handle:
                handle.write("Line %d.\n" % n)
            self.commit("append %d" % n)
        level, text = self.check_line(self.doctor(), "git-status-churn")
        self.assertEqual(level, "WARN", text)
        self.assertIn("over 12 commits", text)
        self.assertIn("appended to, not rewritten", text)
        self.assertRegex(text, r"deleted/added = 0/\d+ = 0\.00")

    def test_rewritten_status_history_passes(self):
        """The same commit count, but each one replaces the current state."""
        self.write_status("Phase 1.")
        self.commit("install")
        for n in range(2, 13):
            self.write_status("Phase %d." % n)
            self.commit("rewrite %d" % n)
        level, text = self.check_line(self.doctor(), "git-status-churn")
        self.assertEqual(level, "PASS", text)
        self.assertIn("over 12 commits", text)
        self.assertIn("STATUS is being rewritten", text)

    def test_register_below_the_repository_root_is_reported(self):
        below = self.project / "app"
        below.mkdir()
        seed_register(below)
        self.commit("install")
        level, text = self.check_line(self.doctor(root=below), "git-repository")
        self.assertEqual(level, "INFO")
        self.assertIn("1 level(s) below the repository root", text)


class FreshInstallTests(unittest.TestCase):
    """Mode 1 Install, end to end, against the promise SKILL.md makes in
    "After Install, once": *a fresh install should exit 0 — or 1 only for
    brand-placeholders you chose to leave*. The project is built outside the
    skill repository so that `exit 0` can be asserted literally, with no
    nested-register advisory from the repository above it."""

    # Placeholder rows Install step 1 says to delete outright.
    PLACEHOLDER_ROWS = ("[The ordered queue", "1. **[one-line question", "| | | | |", "| | | |")

    def setUp(self):
        self.project = Path(tempfile.mkdtemp(prefix="doctor-install-")).resolve()
        self.addCleanup(shutil.rmtree, self.project)
        self.docs = self.project / "docs"
        self.docs.mkdir()

    def install(self, brand=False):
        names = ["README.md", "STATUS.md", "ROADMAP.md", "CHANGELOG.md",
                 "DECISIONS.md", "GLOSSARY.md"]
        if brand:
            names.append("BRAND.md")
        for name in names:
            text = (ROOT / "templates" / name).read_text(encoding="utf-8")
            # Step 1: "Replace every YYYY-MM-DD with today's date. Delete
            # placeholder rows that have no real content."
            text = text.replace("YYYY-MM-DD", TODAY)
            kept = [line for line in text.split("\n")
                    if not any(line.strip().startswith(head) for head in self.PLACEHOLDER_ROWS)]
            (self.docs / name).write_text("\n".join(kept), encoding="utf-8")
        if brand:
            brand_path = self.docs / "BRAND.md"
            brand_path.write_text(brand_path.read_text().replace(
                "Primary color: `[POPULATE]`", "Primary color: `#284B63`"), encoding="utf-8")
        # Step 1 again: personalize what the templates leave bracketed.
        status = (self.docs / "STATUS.md").read_text(encoding="utf-8")
        status = (status
                  .replace("**[Phase name — e.g., Phase 1 — Alignment]**", "**Phase 1 — Alignment**")
                  .replace("[One paragraph on what this phase is producing and its scope "
                           "boundaries. Keep to 2–4 sentences, present tense.]",
                           "Shaping the first release. Scope stops at the ingest path."))
        self.assertNotIn("[Phase name", status)
        (self.docs / "STATUS.md").write_text(status, encoding="utf-8")
        changelog = (self.docs / "CHANGELOG.md").read_text(encoding="utf-8")
        head, _, _ = changelog.partition("Installed the project-docs-protocol at")
        # Step 4: the real installation entry replaces the template's.
        (self.docs / "CHANGELOG.md").write_text(
            head + "Installed the project-docs-protocol at `docs/`. Seeded empty for a true "
                   "cold start. BRAND.md %s.\n" % ("kept with one pending value" if brand
                                                   else "omitted; no brand dimension"),
            encoding="utf-8")
        # Step 2: the block SKILL.md tells the installer to paste, verbatim.
        block = install_wiring_block("docs")
        for name in ("CLAUDE.md", "AGENTS.md"):
            (self.project / name).write_text("# Project\n\n" + block, encoding="utf-8")

    def doctor(self):
        done = subprocess.run([sys.executable, "-B", str(DOCTOR), str(self.project),
                               "--today", TODAY, "--no-git"],
                              capture_output=True, text=True, timeout=60)
        self.assertNotIn("checker error:", done.stderr, done.stdout + done.stderr)
        self.assertNotIn("Traceback", done.stderr, done.stdout + done.stderr)
        return done.returncode, done.stdout

    def complaints(self, output):
        return {name for level, name in
                re.findall(r"^(WARN|FAIL)\s+(\S+)", output, re.M)}

    def test_fresh_install_exits_zero(self):
        self.install()
        code, output = self.doctor()
        self.assertEqual(self.complaints(output), set(), output)
        self.assertEqual(code, 0, output)

    def test_fresh_install_keeping_brand_warns_only_about_placeholders(self):
        self.install(brand=True)
        code, output = self.doctor()
        self.assertEqual(self.complaints(output), {"brand-placeholders"}, output)
        self.assertEqual(code, 1, output)

    def test_install_step_two_block_is_what_doctor_looks_for(self):
        """The pasted block must satisfy every wiring check on its own."""
        self.install()
        _, output = self.doctor()
        for check in ("wiring-block", "wiring-clauses", "wiring-path", "readme-footer"):
            self.assertRegex(output, r"(?m)^PASS\s+%s\s" % re.escape(check))


if __name__ == "__main__":
    unittest.main()
