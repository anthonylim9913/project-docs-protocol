"""Executable STATUS adoption and interrupted-write regression cases."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/docs-migrate.py"
SPEC = importlib.util.spec_from_file_location("docs_migrate", SCRIPT)
MIGRATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATE)
TODAY = "2026-09-10"
HEADER = "| ID | P | Status | Date | Title | Tags | Closes-when | Blocked-on | Touches | Evidence |\n|---|---|---|---|---|---|---|---|---|---|\n"


class MigrationTests(unittest.TestCase):
    def test_twenty_findings_review_write_and_fresh_plan_preserve_all_sources(self):
        source = (ROOT / "tests/fixtures/migration-20/STATUS.md").read_bytes()
        (self.docs / "STATUS.md").write_bytes(source)
        plan = self.reviewed()
        self.assertEqual(plan["counts"]["source_records"], 20)
        self.assertEqual(plan["counts"]["new_rows"], 20)
        self.assertEqual(plan["unmapped"], [])
        self.apply(plan)
        ledger = (self.docs / "LEDGER.md").read_text()
        rows = [line for line in ledger.splitlines() if "migration:STATUS.md#" in line]
        self.assertEqual(len(rows), 20)
        for number in range(1, 21):
            expected_title = f"anonymised finding {number:02d}"
            self.assertEqual(sum(expected_title in line for line in rows), 1)
            self.assertIn(f"| LG-{number:04d} |", rows[number - 1])
        self.assertEqual(source, (self.docs / "STATUS.md").read_bytes())
        fresh = self.plan()
        self.assertEqual(fresh["counts"]["new_rows"], 0)
        self.assertEqual(len(fresh["mappings"]), 20)
        before = self.snapshot()
        self.apply(fresh)
        self.assertEqual(before, self.snapshot())

    def setUp(self):
        scratch = ROOT / "tests/.tmp"
        scratch.mkdir(exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="migration-", dir=scratch))
        self.addCleanup(shutil.rmtree, self.root)
        self.docs = self.root / "docs"
        self.docs.mkdir()
        (self.docs / "DECISIONS.md").write_text("# DECISIONS\n", encoding="utf-8")
        (self.docs / "STATUS.md").write_text("# STATUS\n\n## Known issues\n\n- Cache misses invalidate the current page.\n", encoding="utf-8")
        (self.docs / "CHANGELOG.md").write_text("# CHANGELOG\n\n## 2026-09-09 — previous entry\n\nPreserve this history.\n", encoding="utf-8")

    def plan(self):
        return MIGRATE.build_plan(self.docs, TODAY)

    def reviewed(self, plan=None):
        plan = plan or self.plan()
        for mapping in plan["mappings"]:
            if mapping["existing"]:
                continue
            mapping["reviewed"] = True
            mapping["row"]["closes_when"] = "Cache fixture passes without losing page state."
        return plan

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.docs.iterdir() if p.is_file()}

    def apply(self, plan):
        MIGRATE.apply_plan(self.docs, plan, TODAY)

    def test_preview_keeps_registers_byte_identical(self):
        before = self.snapshot()
        plan = self.plan()
        self.assertEqual(before, self.snapshot())
        self.assertEqual(plan["counts"]["source_records"], 1)
        self.assertEqual(plan["counts"]["new_rows"], 1)
        self.assertFalse(plan["mappings"][0]["reviewed"])

    def test_skips_headers_boilerplate_and_historical_sections(self):
        (self.docs / "STATUS.md").write_text("# STATUS\n\n*Snapshot of current work.*\n\n## Current phase\n\n**Repair completed**\n\n## In flight\n\n| Item | Owner | Target | Notes |\n|---|---|---|---|\n| Cache invalidation fails | agent | today | preserve page |\n\n## Blocked\n\n*No items.*\n\n## Completed\n\n- Historical defect already fixed.\n", encoding="utf-8")
        plan = self.plan()
        self.assertEqual(plan["counts"]["source_records"], 1)
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertIn("preserve page", plan["mappings"][0]["source"]["text"])
        self.assertEqual(plan["unmapped"], [])

    def test_live_prose_requires_documented_disposition(self):
        with (self.docs / "STATUS.md").open("a", encoding="utf-8") as handle:
            handle.write("\nThe deployment problem still needs interpretation.\n")
        plan = self.reviewed()
        self.assertEqual(len(plan["unmapped"]), 1)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "unmapped|disposition"):
            self.apply(plan)
        self.assertEqual(before, self.snapshot())
        plan["unmapped"][0]["disposition"] = "context"
        plan["unmapped"][0]["reason"] = "Context for the cache finding, no separate closing condition."
        self.apply(plan)
        self.assertIn("Context for the cache", (self.docs / "CHANGELOG.md").read_text())

    def test_write_refuses_unreviewed_rows_and_empty_conditions(self):
        plan = self.plan()
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "review"):
            self.apply(plan)
        plan["mappings"][0]["reviewed"] = True
        with self.assertRaisesRegex(ValueError, "closes_when"):
            self.apply(plan)
        self.assertEqual(before, self.snapshot())

    def test_blocked_source_requires_explicit_gate(self):
        path = self.docs / "STATUS.md"
        path.write_text(path.read_text().replace("Known issues", "Blocked"), encoding="utf-8")
        plan = self.reviewed()
        self.assertEqual(plan["mappings"][0]["row"]["status"], "BLOCKED")
        with self.assertRaisesRegex(ValueError, "blocked_on"):
            self.apply(plan)
        plan["mappings"][0]["row"]["blocked_on"] = "owner; provider quota reset"
        self.apply(plan)
        self.assertIn("owner; provider quota reset", (self.docs / "LEDGER.md").read_text())

    def test_allocates_after_archive_and_reservation_aliases(self):
        (self.docs / "LEDGER.md").write_text(HEADER + "| LG-1 | P2 | OPEN | 2026-09-10 | Existing finding | | check | | src | origin |\n")
        (self.docs / "LEDGER-ARCHIVE.md").write_text(HEADER + "| LG-0009 | P2 | CLOSED | 2026-09-10 | Archived finding | | check | | src | committed |\n")
        (self.docs / "RESERVATIONS.md").write_text("Reserved ledger IDs: LG-0010–LG-0012\n")
        plan = self.reviewed()
        self.assertEqual(plan["mappings"][0]["id"], "LG-0013")
        self.apply(plan)
        self.assertIn("LG-0013", (self.docs / "LEDGER.md").read_text())

    def test_oversized_reservation_is_controlled_error(self):
        (self.docs / "RESERVATIONS.md").write_text("LG-" + "9" * 5000)
        with self.assertRaisesRegex(ValueError, "ID|identifier"):
            self.plan()

    def test_real_dates_and_escaped_source_cells(self):
        (self.docs / "STATUS.md").write_text("## Known issues\n- Cache | page state requires preservation.\n")
        plan = self.reviewed()
        self.apply(plan)
        output = (self.docs / "LEDGER.md").read_text()
        self.assertNotIn("YYYY-MM-DD |", output)
        self.assertIn("| 2026-09-10 |", output)
        self.assertIn("Cache \\| page", output)
        self.assertNotIn("define a yes/no close condition", output)
        for index, invalid in enumerate(("YYYY-MM-DD", "2026-02-30", "2027-01-01")):
            with self.subTest(date=invalid):
                changed = self.reviewed()
                # A new finding exercises validation after initial migration.
                with (self.docs / "STATUS.md").open("a") as handle:
                    handle.write("- Another cache issue " + str(index) + "\n")
                changed = self.reviewed()
                changed["mappings"][-1]["row"]["date"] = invalid
                with self.assertRaisesRegex(ValueError, "date"):
                    self.apply(changed)

    def test_same_plan_and_fresh_plan_are_byte_idempotent(self):
        plan = self.reviewed()
        source = (self.docs / "STATUS.md").read_bytes()
        old_log = (self.docs / "CHANGELOG.md").read_bytes()
        self.apply(plan)
        first = self.snapshot()
        self.apply(plan)
        self.assertEqual(first, self.snapshot())
        fresh = self.plan()
        self.assertEqual(fresh["counts"]["new_rows"], 0)
        self.assertTrue(fresh["mappings"][0]["existing"])
        self.apply(fresh)
        self.assertEqual(first, self.snapshot())
        self.assertEqual(source, (self.docs / "STATUS.md").read_bytes())
        self.assertTrue((self.docs / "CHANGELOG.md").read_bytes().endswith(old_log))

    def test_source_identity_survives_reordering_and_archival(self):
        plan = self.reviewed()
        self.apply(plan)
        ledger = (self.docs / "LEDGER.md").read_text()
        row = next(line for line in ledger.splitlines() if "migration:STATUS.md#" in line)
        (self.docs / "LEDGER-ARCHIVE.md").write_text(HEADER + row.replace("OPEN", "CLOSED") + "\n")
        (self.docs / "LEDGER.md").write_text(ledger.replace(row + "\n", ""))
        status = self.docs / "STATUS.md"
        status.write_text("\n\n" + status.read_text())
        fresh = self.plan()
        self.assertEqual(fresh["counts"]["new_rows"], 0)
        self.assertEqual(fresh["mappings"][0]["id"], plan["mappings"][0]["id"])

    def test_source_and_reservation_drift_block_without_mutation(self):
        for filename in ("STATUS.md", "RESERVATIONS.md", "LEDGER-ARCHIVE.md"):
            with self.subTest(filename=filename):
                plan = self.reviewed()
                path = self.docs / filename
                path.write_text((path.read_text() if path.exists() else "") + "\nLG-9999 new record\n")
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "changed|drift"):
                    self.apply(plan)
                self.assertEqual(before, self.snapshot())
                path.unlink()
                if filename == "STATUS.md":
                    path.write_text("## Known issues\n- Cache misses invalidate the current page.\n")

    def test_dropped_mapping_cannot_be_hidden_by_review(self):
        plan = self.reviewed()
        plan["mappings"] = []
        with self.assertRaisesRegex(ValueError, "mapping|inventory"):
            self.apply(plan)

    def test_interruption_after_log_replays_once(self):
        plan = self.reviewed()
        original = MIGRATE.atomic_write
        def interrupt(path, content):
            if path.name == "LEDGER.md":
                raise OSError("simulated disk failure before ledger replacement")
            original(path, content)
        with mock.patch.object(MIGRATE, "atomic_write", side_effect=interrupt):
            with self.assertRaises(OSError):
                self.apply(plan)
        self.assertFalse((self.docs / "LEDGER.md").exists())
        partial_log = (self.docs / "CHANGELOG.md").read_bytes()
        self.assertIn(b"source-to-ID", partial_log)
        self.apply(plan)
        self.assertEqual(partial_log, (self.docs / "CHANGELOG.md").read_bytes())
        first = self.snapshot()
        self.apply(plan)
        self.assertEqual(first, self.snapshot())

    def test_interruption_after_ledger_replays_once(self):
        plan = self.reviewed()
        original = MIGRATE.atomic_write
        def interrupt(path, content):
            original(path, content)
            if path.name == "LEDGER.md":
                raise OSError("simulated interruption after ledger replacement")
        with mock.patch.object(MIGRATE, "atomic_write", side_effect=interrupt):
            with self.assertRaises(OSError):
                self.apply(plan)
        output = (self.docs / "LEDGER.md").read_bytes()
        self.apply(plan)
        self.assertEqual(output, (self.docs / "LEDGER.md").read_bytes())
        self.assertEqual((self.docs / "CHANGELOG.md").read_text().count("source-to-ID"), 1)

    def test_replay_refuses_conflicting_intervening_edit(self):
        plan = self.reviewed()
        original = MIGRATE.atomic_write
        def interrupt(path, content):
            if path.name == "LEDGER.md":
                raise OSError("simulated interruption")
            original(path, content)
        with mock.patch.object(MIGRATE, "atomic_write", side_effect=interrupt):
            with self.assertRaises(OSError):
                self.apply(plan)
        with (self.docs / "CHANGELOG.md").open("a") as handle:
            handle.write("Concurrent writer added this.\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "conflict|changed"):
            self.apply(plan)
        self.assertEqual(before, self.snapshot())


    def test_cli_write_without_plan_preserves_every_source(self):
        before = self.snapshot()
        process = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.root), "--write"], capture_output=True, text=True)
        self.assertEqual(process.returncode, 2, process.stderr)
        self.assertNotIn("Traceback", process.stderr)
        self.assertEqual(before, self.snapshot())

    def test_cli_plan_cannot_overwrite_journal_slot(self):
        before = self.snapshot()
        process = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.root), "--plan", str(self.docs / MIGRATE.JOURNAL)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 2, process.stderr)
        self.assertEqual(before, self.snapshot())

    def test_corrupt_journal_is_a_controlled_error(self):
        plan = self.reviewed()
        self.apply(plan)
        path = self.docs / MIGRATE.JOURNAL
        journal = json.loads(path.read_text())
        journal["targets"] = {}
        journal["order"] = []
        path.write_text(json.dumps(journal))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "journal"):
            self.apply(plan)
        self.assertEqual(before, self.snapshot())

    def test_failure_before_log_leaves_registers_untouched(self):
        plan = self.reviewed()
        before = self.snapshot()
        original = MIGRATE.atomic_write
        def interrupt(path, content):
            if path.name == "CHANGELOG.md":
                raise OSError("simulated interruption before log")
            original(path, content)
        with mock.patch.object(MIGRATE, "atomic_write", side_effect=interrupt):
            with self.assertRaises(OSError):
                self.apply(plan)
        for name, content in before.items():
            self.assertEqual(content, (self.docs / name).read_bytes())
        self.assertFalse((self.docs / "LEDGER.md").exists())
        self.assertTrue((self.docs / MIGRATE.JOURNAL).is_file())
        self.apply(plan)
        self.assertEqual((self.docs / "LEDGER.md").read_text().count("migration:STATUS.md#"), 1)

    def test_generated_ledger_passes_doctor_schema(self):
        (self.root / "AGENTS.md").write_text((ROOT / "AGENTS.md").read_text())
        (self.docs / "README.md").write_text("*Installed via the `project-docs-protocol` skill.*\n")
        (self.docs / "DECISIONS.md").write_text("# DECISIONS\n")
        plan = self.reviewed()
        self.apply(plan)
        process = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/docs-doctor.py"), str(self.root), "--today", TODAY, "--no-git"], capture_output=True, text=True)
        self.assertNotIn("Traceback", process.stderr)
        self.assertRegex(process.stdout, r"PASS\s+ledger-header")
        self.assertRegex(process.stdout, r"PASS\s+ledger-schema")
        self.assertRegex(process.stdout, r"PASS\s+ledger-stale-open")



    def test_live_archive_alias_conflict_blocks_migration(self):
        (self.docs / "LEDGER.md").write_text(HEADER + "| LG-1 | P2 | OPEN | 2026-09-10 | New occupant | | check | | src | origin |\n")
        (self.docs / "LEDGER-ARCHIVE.md").write_text(HEADER + "| LG-0001 | P2 | CLOSED | 2026-09-10 | Old occupant | | check | | src | committed |\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "collision|archive"):
            self.plan()
        self.assertEqual(before, self.snapshot())

    def test_prefixed_series_do_not_collide_with_default_allocation(self):
        (self.docs / "LEDGER.md").write_text("Family prefix: UI-LG-0001\n\n" + HEADER + "| UI-LG-0001 | P2 | OPEN | 2026-09-10 | UI issue | | check | | src | origin |\n")
        plan = self.reviewed()
        self.assertEqual(plan["mappings"][0]["id"], "LG-0001")
        self.apply(plan)
        self.assertIn("| UI-LG-0001 |", (self.docs / "LEDGER.md").read_text())
        self.assertIn("| LG-0001 |", (self.docs / "LEDGER.md").read_text())

    def test_oversized_zero_padded_reservation_is_rejected(self):
        for digits in ("0" * 13, "0" * 5000 + "1"):
            with self.subTest(length=len(digits)):
                (self.docs / "RESERVATIONS.md").write_text("LG-" + digits)
                with self.assertRaisesRegex(ValueError, "ID|identifier"):
                    self.plan()

    def test_inserts_new_rows_before_existing_footer(self):
        footer = "\nArchive policy and local notes stay after this table.\n"
        (self.docs / "LEDGER.md").write_text(HEADER + "| LG-0001 | P2 | OPEN | 2026-09-10 | Existing finding | | check | | src | origin |\n" + footer)
        (self.root / "AGENTS.md").write_text((ROOT / "AGENTS.md").read_text())
        (self.docs / "README.md").write_text("*Installed via the `project-docs-protocol` skill.*\n")
        (self.docs / "DECISIONS.md").write_text("# DECISIONS\n")
        self.apply(self.reviewed())
        text = (self.docs / "LEDGER.md").read_text()
        self.assertTrue(text.endswith(footer))
        process = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/docs-doctor.py"), str(self.root), "--today", TODAY, "--no-git"], capture_output=True, text=True)
        self.assertRegex(process.stdout, r"PASS\s+ledger-header")
        self.assertRegex(process.stdout, r"PASS\s+ledger-schema")



    def test_fenced_comment_literal_cannot_hide_live_finding(self):
        (self.docs / "STATUS.md").write_text("## Known issues\n```html\n<!-- illustrative opener\n```\n- Real live defect.\n")
        plan = self.plan()
        self.assertEqual(plan["counts"]["source_records"], 1)
        self.assertEqual(plan["mappings"][0]["source"]["text"], "- Real live defect.")

    def test_invalid_backtick_info_is_live_text_not_a_fence(self):
        (self.docs / "STATUS.md").write_text("## Known issues\n```invalid`info\n- Real live defect.\n")
        plan = self.plan()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(len(plan["unmapped"]), 1)
        self.assertEqual(plan["mappings"][0]["source"]["text"], "- Real live defect.")

    def test_fence_info_comment_literal_cannot_hide_live_finding(self):
        (self.docs / "STATUS.md").write_text("## Known issues\n```html <!-- literal info\nexample\n```\n- Real live defect.\n")
        self.assertEqual(self.plan()["counts"]["source_records"], 1)

    def test_hidden_only_ledger_table_is_rejected_before_journal(self):
        for opening, closing in (("```markdown\n", "```\n"), ("<!--\n", "-->\n")):
            with self.subTest(opening=opening):
                (self.docs / "LEDGER.md").write_text("# LEDGER\n" + opening + HEADER + closing)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "header|visible"):
                    self.plan()
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.docs / MIGRATE.JOURNAL).exists())

    def test_structured_blocked_row_preserves_state_and_gate(self):
        (self.docs / "STATUS.md").write_text("## In flight\n| Item | Status | Blocked on |\n|---|---|---|\n| Ship parser | BLOCKED | owner |\n")
        plan = self.reviewed()
        row = plan["mappings"][0]["row"]
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["blocked_on"], "owner")
        row["status"], row["blocked_on"] = "OPEN", ""
        with self.assertRaisesRegex(ValueError, "blocked source"):
            self.apply(plan)



    def test_malformed_journal_shapes_exit_cleanly_without_writes(self):
        plan = self.reviewed()
        self.apply(plan)
        plan_path = self.docs / "reviewed-plan.json"
        plan_path.write_text(json.dumps(plan))
        journal_path = self.docs / MIGRATE.JOURNAL
        original = json.loads(journal_path.read_text())
        mutations = [[], {**original, "inputs": list(original["inputs"])}, {**original, "targets": []}, {**original, "targets": {"CHANGELOG.md": []}}, {**original, "state": []}]
        for invalid in mutations:
            with self.subTest(journal=str(invalid)[:80]):
                journal_path.write_text(json.dumps(invalid))
                before = self.snapshot()
                process = subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.root), "--today", TODAY, "--write", "--plan", str(plan_path)], capture_output=True, text=True)
                self.assertEqual(process.returncode, 2, process.stderr)
                self.assertNotIn("Traceback", process.stderr)
                self.assertEqual(before, self.snapshot())



    def test_explicit_source_gates_cannot_be_replaced_during_migration(self):
        (self.docs / "STATUS.md").write_text("## In flight\n| Item | Status | Blocked on |\n|---|---|---|\n| Ship parser | BLOCKED | owner; provider quota |\n")
        plan = self.reviewed()
        plan["mappings"][0]["row"]["blocked_on"] = "provider quota"
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "source gate"):
            self.apply(plan)
        self.assertEqual(before, self.snapshot())

    def test_visible_ledger_table_after_hidden_example_is_used(self):
        hidden = "```markdown\n" + HEADER + "```\n\n"
        footer = "\n<!-- illustrative note only -->\n"
        (self.docs / "LEDGER.md").write_text("# LEDGER\n\n" + hidden + HEADER + footer)
        self.apply(self.reviewed())
        output = (self.docs / "LEDGER.md").read_text()
        self.assertIn(hidden, output)
        self.assertTrue(output.endswith(footer))
        rows = MIGRATE.ledger_rows(output, "LEDGER.md")
        self.assertEqual(len(rows), 1)
        self.assertIn("migration:STATUS.md#", rows[0][-1])



    def test_indented_code_ledger_headers_are_rejected_before_writing(self):
        for indent in ("    ", "\t"):
            with self.subTest(indent=repr(indent)):
                (self.docs / "LEDGER.md").write_text("# LEDGER\n\n" + "".join(indent + line for line in HEADER.splitlines(keepends=True)))
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "header"):
                    self.plan()
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.docs / MIGRATE.JOURNAL).exists())

    def test_zero_to_three_space_ledger_tables_remain_supported(self):
        for width in range(4):
            with self.subTest(spaces=width):
                (self.docs / "LEDGER.md").write_text("# LEDGER\n\n" + "".join(" " * width + line for line in HEADER.splitlines(keepends=True)))
                self.apply(self.reviewed())
                rows = MIGRATE.ledger_rows((self.docs / "LEDGER.md").read_text(), "LEDGER.md")
                self.assertEqual(len(rows), 1)
                self.assertIn("migration:STATUS.md#", rows[0][-1])

    def test_status_code_indented_tables_are_unresolved_not_mapped(self):
        table = "| Item | Status | Blocked on |\n|---|---|---|\n| Ship parser | BLOCKED | owner |\n"
        for indent in ("    ", "\t"):
            with self.subTest(indent=repr(indent)):
                (self.docs / "STATUS.md").write_text("## In flight\n\n" + "".join(indent + line for line in table.splitlines(keepends=True)))
                plan = self.plan()
                self.assertEqual(plan["mappings"], [])
                self.assertEqual(len(plan["unmapped"]), 3)


    def test_cli_review_write_and_replay(self):
        plan_path = self.docs / "migration-plan.json"
        base = [sys.executable, "-B", str(SCRIPT), str(self.root), "--today", TODAY]
        process = subprocess.run(base + ["--plan", str(plan_path)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        plan = self.reviewed(json.loads(plan_path.read_text()))
        plan_path.write_text(json.dumps(plan))
        for _ in range(2):
            process = subprocess.run(base + ["--write", "--plan", str(plan_path)], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual((self.docs / "LEDGER.md").read_text().count("migration:STATUS.md#"), 1)

    def test_extra_column_does_not_disable_status_and_gate_extraction(self):
        (self.docs / "STATUS.md").write_text(
            "## In flight\n| Item | Status | Blocked on | Severity |\n|---|---|---|---|\n"
            "| Provider quota exhausted | BLOCKED | owner; provider quota | P0 |\n", encoding="utf-8")
        plan = self.plan()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(plan["unmapped"], [])
        source = plan["mappings"][0]["source"]
        self.assertIn("Provider quota exhausted", source["text"])
        self.assertEqual(source["status"], "BLOCKED")
        self.assertEqual(source["blocked_on"], "owner; provider quota")
        row = plan["mappings"][0]["row"]
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["blocked_on"], "owner; provider quota")

    def test_header_and_delimiter_rows_never_become_records(self):
        for labels in ("| Item | Status | Blocked on | Severity |", "| Alpha | Beta | Gamma |"):
            with self.subTest(labels=labels):
                width = labels.count("|") - 1
                (self.docs / "STATUS.md").write_text(
                    "## In flight\n" + labels + "\n|" + "---|" * width + "\n"
                    + "| one |" + " OPEN |" * (width - 1) + "\n", encoding="utf-8")
                plan = self.plan()
                self.assertEqual(plan["counts"]["source_records"], 1)
                # Which bucket the data row lands in is another test's subject;
                # this one is only about the header and delimiter rows.
                records = plan["mappings"] + plan["unmapped"]
                self.assertEqual(len(records), 1)
                self.assertIn("one", records[0]["source"]["text"])
                for record in records:
                    self.assertNotIn("---", record["source"]["text"])
                    self.assertNotEqual(record["source"]["text"], labels)

    def test_template_blocked_layout_preserves_its_gate(self):
        (self.docs / "STATUS.md").write_text(
            "## Blocked\n| Item | Blocked by | Unblocks when |\n|---|---|---|\n"
            "| Ship parser | owner sign-off | owner answers the question |\n", encoding="utf-8")
        plan = self.plan()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(plan["unmapped"], [])
        self.assertEqual(plan["mappings"][0]["source"]["blocked_on"], "owner sign-off")
        self.assertEqual(plan["mappings"][0]["row"]["status"], "BLOCKED")
        self.assertEqual(plan["mappings"][0]["row"]["blocked_on"], "owner sign-off")

    def test_unnamed_columns_carrying_a_state_token_stay_unresolved(self):
        """A layout we cannot read must not silently downgrade BLOCKED to OPEN."""
        (self.docs / "STATUS.md").write_text(
            "## In flight\n| Alpha | Beta | Gamma |\n|---|---|---|\n"
            "| Ship parser | BLOCKED | owner |\n", encoding="utf-8")
        plan = self.plan()
        self.assertEqual(plan["mappings"], [])
        self.assertEqual(len(plan["unmapped"]), 1)
        self.assertIn("Ship parser", plan["unmapped"][0]["source"]["text"])

    def test_unnamed_columns_without_a_state_token_still_map(self):
        """The guard is about ambiguity, not about unfamiliar labels as such."""
        (self.docs / "STATUS.md").write_text(
            "## In flight\n| Alpha | Beta | Gamma |\n|---|---|---|\n"
            "| Ship parser | today | web/ |\n", encoding="utf-8")
        plan = self.plan()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(plan["unmapped"], [])

    def test_pipe_rows_without_a_delimiter_are_unresolved_not_mapped(self):
        (self.docs / "STATUS.md").write_text(
            "## In flight\n| Item | Status | Blocked on |\n| Ship parser | BLOCKED | owner |\n", encoding="utf-8")
        plan = self.plan()
        self.assertEqual(plan["mappings"], [])
        self.assertEqual(len(plan["unmapped"]), 2)

    def test_register_is_found_the_way_the_doctor_finds_it(self):
        root = Path(tempfile.mkdtemp(dir=self.root))
        (root / "docs").mkdir()
        (root / "DECISIONS.md").write_text("# DECISIONS\n")
        (root / "STATUS.md").write_text("## In flight\n\n- Cache misses invalidate the page.\n", encoding="utf-8")
        (root / "CHANGELOG.md").write_text("# CHANGELOG\n\n## 2026-09-09 — previous entry\n\nKeep.\n", encoding="utf-8")
        process = subprocess.run([sys.executable, "-B", str(SCRIPT), str(root), "--today", TODAY], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        self.assertIn("Cache misses", process.stdout)
        self.assertEqual(MIGRATE.register_dir(root), root)

    def test_docs_register_is_found_from_the_root_and_when_handed_directly(self):
        self.assertEqual(MIGRATE.register_dir(self.root), self.docs)
        self.assertEqual(MIGRATE.register_dir(self.docs), self.docs)
        for target in (self.root, self.docs):
            with self.subTest(target=target.name):
                process = subprocess.run([sys.executable, "-B", str(SCRIPT), str(target), "--today", TODAY], capture_output=True, text=True)
                self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
                self.assertIn("Cache misses", process.stdout)


if __name__ == "__main__":
    unittest.main()
