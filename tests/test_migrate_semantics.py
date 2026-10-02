"""Reviewed-write regressions for source state, gates, and opaque examples."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/docs-migrate.py"
SPEC = importlib.util.spec_from_file_location("migrate_semantics", SCRIPT)
MIGRATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATE)
TODAY = "2026-09-11"


class MigrationSemanticsTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / "tests/.tmp"
        scratch.mkdir(exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="semantics-", dir=scratch))
        self.addCleanup(shutil.rmtree, self.root)
        self.docs = self.root / "docs"
        self.docs.mkdir()
        (self.docs / "CHANGELOG.md").write_text("# CHANGELOG\n\n## 2026-09-11 — installed documentation\n\nPreserve this entry.\n")
        (self.docs / "DECISIONS.md").write_text("# DECISIONS\n")

    def source(self, text):
        (self.docs / "STATUS.md").write_text("# STATUS\n\n## In flight\n\n" + text)

    def table(self, labels, values):
        self.source("| " + " | ".join(labels) + " |\n|" + "---|" * len(labels) + "\n| " + " | ".join(values) + " |\n")

    def reviewed(self):
        plan = MIGRATE.build_plan(self.docs, TODAY)
        for mapping in plan["mappings"]:
            if not mapping["existing"]:
                mapping["reviewed"] = True
                mapping["row"]["closes_when"] = "Parser acceptance fixture passes after all named gates are resolved."
        return plan

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.docs.iterdir() if p.is_file()}

    def cli(self, plan):
        plan_path = self.root / "reviewed-plan.json"
        plan_path.write_text(json.dumps(plan))
        return subprocess.run([sys.executable, "-B", str(SCRIPT), str(self.root), "--today", TODAY,
                               "--write", "--plan", str(plan_path)], capture_output=True, text=True)

    def apply(self, plan):
        source = (self.docs / "STATUS.md").read_bytes()
        MIGRATE.validate_plan(self.docs, plan, TODAY)
        result = self.cli(plan)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.docs / "STATUS.md").read_bytes(), source)
        first = self.snapshot()
        result = self.cli(plan)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(first, self.snapshot())
        fresh = MIGRATE.build_plan(self.docs, TODAY)
        self.assertEqual(fresh["counts"]["new_rows"], 0)
        MIGRATE.apply_plan(self.docs, fresh, TODAY)
        self.assertEqual(first, self.snapshot())
        return (self.docs / "LEDGER.md").read_text()

    def assert_refused(self, plan, pattern):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, pattern):
            MIGRATE.validate_plan(self.docs, plan, TODAY)
        result = self.cli(plan)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.docs / MIGRATE.JOURNAL).exists())

    def test_secondary_nonempty_gate_is_preserved_in_reviewed_write(self):
        self.table(["Item", "Status", "Blocked on", "Gate"], ["Ship parser", "OPEN", "", "owner sign-off"])
        plan = self.reviewed()
        self.assertEqual(plan["mappings"][0]["row"]["status"], "BLOCKED")
        self.assertEqual(plan["mappings"][0]["row"]["blocked_on"], "owner sign-off")
        ledger = self.apply(plan)
        self.assertIn("| BLOCKED |", ledger)
        self.assertIn("| owner sign-off |", ledger)

    def test_conflicting_state_aliases_require_source_reconciliation_before_write(self):
        self.table(["Item", "Status", "State"], ["Ship parser", "OPEN", "BLOCKED"])
        plan = self.reviewed()
        self.assertEqual(plan["mappings"], [])
        self.assertEqual(len(plan["unmapped"]), 1)
        self.assertIn("OPEN | BLOCKED", plan["unmapped"][0]["source"]["text"])
        self.assert_refused(plan, "unmapped|disposition")
        self.table(["Item", "Status", "Blocked on"], ["Ship parser", "BLOCKED", "owner approval"])
        self.assertIn("| owner approval |", self.apply(self.reviewed()))

    def test_html_disposition_logs_content_without_inserting_source_headings(self):
        self.source("<pre>\n## Findings\n- Example finding.\n</pre>\n")
        plan = self.reviewed()
        self.assertEqual(plan["mappings"], [])
        self.assertEqual(len(plan["unmapped"]), 1)
        plan["unmapped"][0].update(disposition="context", reason="Illustrative example, no current finding.")
        self.apply(plan)
        log = (self.docs / "CHANGELOG.md").read_text()
        self.assertNotIn("\n## Findings\n", log)
        self.assertIn("Example finding", log)

    def test_every_gate_alias_survives_and_cannot_be_removed_during_review(self):
        self.table(["Item", "Status", "Blocked on", "Blocked by"],
                   ["Ship parser", "BLOCKED", "provider quota", "owner approval"])
        plan = self.reviewed()
        self.assertEqual(plan["mappings"][0]["row"]["blocked_on"], "provider quota; owner approval")
        for retained in ("provider quota", "owner approval"):
            with self.subTest(retained=retained):
                changed = copy.deepcopy(plan)
                changed["mappings"][0]["row"]["blocked_on"] = retained
                self.assert_refused(changed, "source gate")
        self.assertIn("| provider quota; owner approval |", self.apply(plan))

    def test_matching_state_aliases_and_empty_aliases_are_supported(self):
        self.table(["Item", "Status", "State", "Blocked on", "Gate"],
                   ["Ship parser", "BLOCKED", "**BLOCKED**", "owner approval", ""])
        self.assertIn("| owner approval |", self.apply(self.reviewed()))

    def test_invalid_secondary_state_remains_unresolved(self):
        self.table(["Item", "Status", "State"], ["Ship parser", "OPEN", "pending decision"])
        plan = self.reviewed()
        self.assertEqual(plan["mappings"], [])
        self.assert_refused(plan, "unmapped|disposition")

    def test_formatted_state_in_unknown_layout_requires_reconciliation(self):
        for state in ("**BLOCKED**", "__BLOCKED__", "*BLOCKED*", "_BLOCKED_", "`BLOCKED`", "``BLOCKED``", "~~BLOCKED~~"):
            with self.subTest(state=state):
                self.table(["Alpha", "Beta", "Gamma"], ["Ship parser", state, "owner"])
                plan = self.reviewed()
                self.assertEqual(plan["mappings"], [])
                self.assertIn(state, plan["unmapped"][0]["source"]["text"])
                self.assert_refused(plan, "unmapped|disposition")

    def test_unsupported_state_markup_is_visible_for_reconciliation(self):
        for state in ("<strong>BLOCKED</strong>", "[BLOCKED](status.md)", "**BLOCKED", "&#66;LOCKED"):
            with self.subTest(state=state):
                self.table(["Alpha", "Beta", "Gamma"], ["Ship parser", state, "owner"])
                plan = self.reviewed()
                self.assertEqual(plan["mappings"], [])
                self.assertIn(state, plan["unmapped"][0]["source"]["text"])
                self.assert_refused(plan, "unmapped|disposition")

    def test_formatted_known_states_keep_gates_in_actual_write(self):
        states = ("BLOCKED", "**BLOCKED**", "__BLOCKED__", "*BLOCKED*", "_BLOCKED_", "`BLOCKED`", "``BLOCKED``")
        self.source("| Item | Status | Gate |\n|---|---|---|\n" + "".join(
            f"| Ship parser {number} | {state} | owner {number} |\n" for number, state in enumerate(states)))
        plan = self.reviewed()
        self.assertEqual(len(plan["mappings"]), 7)
        ledger = self.apply(plan)
        rows = [line for line in ledger.splitlines() if "migration:STATUS.md#" in line]
        self.assertEqual(len(rows), 7)
        for number, row in enumerate(rows):
            self.assertIn("| BLOCKED |", row)
            self.assertIn(f"| owner {number} |", row)

    def test_ordinary_titles_do_not_invent_state_semantics(self):
        self.source("| Item | Notes |\n|---|---|\n" + "".join(f"| {title} | preserve ordinary title |\n" for title in
                    ("BLOCKED", "**BLOCKED**", "requests blocked by CORS", "An **ordinary** title")))
        plan = self.reviewed()
        self.assertEqual(len(plan["mappings"]), 4)
        self.assertEqual(plan["unmapped"], [])
        self.assertTrue(all(mapping["row"]["status"] == "OPEN" for mapping in plan["mappings"]))
        ledger = self.apply(plan)
        self.assertEqual(sum("migration:STATUS.md#" in line for line in ledger.splitlines()), 4)

    def test_unknown_layout_without_state_still_maps(self):
        self.table(["Alpha", "Beta", "Gamma"], ["Ship parser", "today", "web/"])
        self.assertIn("Ship parser", self.apply(self.reviewed()))

    def test_html_example_is_one_visible_unresolved_record_and_never_a_live_row(self):
        example = "<pre>\n| Item | Status | Gate |\n|---|---|---|\n| Example parser | OPEN | |\n</pre>"
        self.source(example + "\n\n- Real parser finding.\n")
        plan = self.reviewed()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(len(plan["unmapped"]), 1)
        self.assertEqual(plan["unmapped"][0]["source"]["text"], example)
        self.assert_refused(plan, "unmapped|disposition")
        plan["unmapped"][0].update(disposition="context", reason="The preformatted block demonstrates a table and is not current work.")
        ledger = self.apply(plan)
        self.assertNotIn("Example parser", ledger)
        self.assertIn("Real parser finding", ledger)
        self.assertIn("Example parser", (self.docs / "CHANGELOG.md").read_text())

    def test_opaque_html_boundaries_preserve_inner_content_for_reconciliation(self):
        for opening, closing in (("<PRE class=\"sample\">", "</PRE>"), ("<script>", "</script>"),
                                 ("<style>", "</style>"), ("<textarea>", "</textarea>"), ("<div>", "</div>")):
            with self.subTest(opening=opening):
                self.source(opening + "\n\n## Findings\n- Example finding.\n" + closing + "\n\n- Actual finding.\n")
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertEqual(plan["mappings"][0]["source"]["text"], "- Actual finding.")
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("- Example finding.", plan["unmapped"][0]["source"]["text"])
                self.assert_refused(plan, "unmapped|disposition")

    def test_unclosed_html_example_is_preserved_without_inner_live_mappings(self):
        self.source("<pre>\n| Item | Notes |\n|---|---|\n| Example parser | demo |\n\n## Findings\n- Still example content.\n")
        plan = self.reviewed()
        self.assertEqual(plan["mappings"], [])
        self.assertEqual(len(plan["unmapped"]), 1)
        self.assertIn("Still example content", plan["unmapped"][0]["source"]["text"])
        self.assert_refused(plan, "unmapped|disposition")

    def test_nested_html_does_not_release_inner_example_as_live_content(self):
        self.source("<div>\n<div>\nInner example\n</div>\n\n- Still example content.\n</div>\n\n- Actual finding.\n")
        plan = self.reviewed()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(plan["mappings"][0]["source"]["text"], "- Actual finding.")
        self.assertEqual(len(plan["unmapped"]), 1)
        self.assertIn("Still example content", plan["unmapped"][0]["source"]["text"])
        self.assert_refused(plan, "unmapped|disposition")

    def test_html_comment_and_attribute_tags_do_not_release_example_content(self):
        for literal in ('<!-- </div> -->', '<!--\n</div>\n-->', '<!-- <div> -->',
                        '<span title="</div>">note</span>', "<span title='<div>'>note</span>",
                        '<span title="\n</div>\n">note</span>'):
            with self.subTest(literal=literal):
                self.source("<div>\n" + literal + "\n\n| Item | Notes |\n|---|---|\n| Example parser | demo |\n</div>\n\n- Actual finding.\n")
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertEqual(plan["mappings"][0]["source"]["text"], "- Actual finding.")
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("Example parser", plan["unmapped"][0]["source"]["text"])
                self.assert_refused(plan, "unmapped|disposition")

    def test_comment_in_html_example_cannot_expose_ledger_write_target(self):
        self.source("- Actual finding.\n")
        (self.docs / "LEDGER.md").write_text("# LEDGER\n\n<div>\n<!-- </div> -->\n\n" + MIGRATE.HEADER + "</div>\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "header|visible"):
            self.reviewed()
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.docs / MIGRATE.JOURNAL).exists())

    def test_reviewed_html_example_disposition_writes_only_real_finding(self):
        self.source("<div>\n<!-- </div> -->\n\n| Item | Notes |\n|---|---|\n| Example parser | demo |\n</div>\n\n- Actual finding.\n")
        plan = self.reviewed()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(len(plan["unmapped"]), 1)
        plan["unmapped"][0].update(disposition="context", reason="HTML example has no current finding.")
        ledger = self.apply(plan)
        self.assertNotIn("Example parser", ledger)
        self.assertIn("Actual finding", ledger)

    def test_raw_html_keeps_quoted_opener_and_first_closing_tag_contract(self):
        for tag in ("pre", "script", "style", "textarea"):
            with self.subTest(tag=tag):
                self.source(f'<{tag} title="</{tag}>">\n- Example finding.\n<!-- </{tag}> -->\n\n- Actual finding.\n')
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertEqual(plan["mappings"][0]["source"]["text"], "- Actual finding.")
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("Example finding", plan["unmapped"][0]["source"]["text"])

    def test_multiline_void_attributes_cannot_become_source_or_ledger_tables(self):
        for tag in ("img", "br", "input"):
            with self.subTest(tag=tag):
                self.source(f'<{tag}\n title="\n| Item | Notes |\n|---|---|\n| Example parser | demo |\n">\n\n- Actual finding.\n')
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertEqual(plan["mappings"][0]["source"]["text"], "- Actual finding.")
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("Example parser", plan["unmapped"][0]["source"]["text"])
                ledger_path = self.docs / "LEDGER.md"
                ledger_path.write_text(f'# LEDGER\n\n<{tag}\n title="\n' + MIGRATE.HEADER + '">\n')
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "header|visible"):
                    self.reviewed()
                self.assertEqual(before, self.snapshot())
                ledger_path.unlink()

    def test_adjacent_html_roots_and_partial_openers_remain_opaque(self):
        for opening, closing in (("<div></div><pre>", "</pre>"), ("<div></div><div>", "</div>"),
                                 ("<div></div><pre\n class=\"example\">", "</pre>")):
            with self.subTest(opening=opening):
                self.source(opening + "\n| Item | Notes |\n|---|---|\n| Example parser | demo |\n" + closing + "\n\n- Actual finding.\n")
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertEqual(plan["mappings"][0]["source"]["text"], "- Actual finding.")
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("Example parser", plan["unmapped"][0]["source"]["text"])
                ledger_path = self.docs / "LEDGER.md"
                ledger_path.write_text("# LEDGER\n\n" + opening + "\n" + MIGRATE.HEADER + closing + "\n")
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "header|visible"):
                    self.reviewed()
                self.assertEqual(before, self.snapshot())
                ledger_path.unlink()

    def test_nonraw_html_uses_blank_line_boundary_before_following_table(self):
        table = "| Item | Notes |\n|---|---|\n| Example parser | demo |\n"
        for opener in ("<br>", "<div></div>"):
            with self.subTest(opener=opener):
                self.source(opener + "\n" + table)
                plan = self.reviewed()
                self.assertEqual(plan["mappings"], [])
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("Example parser", plan["unmapped"][0]["source"]["text"])
                self.assert_refused(plan, "unmapped|disposition")
                self.source(opener + "\n\n" + table)
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertIn("Example parser", plan["mappings"][0]["source"]["text"])
                self.assertEqual(len(plan["unmapped"]), 1)

    def test_raw_html_close_does_not_require_blank_line_before_live_table(self):
        self.source("<pre>\nExample content.\n</pre>\n| Item | Notes |\n|---|---|\n| Actual parser | live |\n")
        plan = self.reviewed()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertIn("Actual parser", plan["mappings"][0]["source"]["text"])
        self.assertEqual(len(plan["unmapped"]), 1)
        self.assertEqual(plan["unmapped"][0]["source"]["text"], "<pre>\nExample content.\n</pre>")

    def test_html_ledger_example_is_not_an_accepted_write_target(self):
        self.source("- Actual finding.\n")
        (self.docs / "LEDGER.md").write_text("# LEDGER\n\n<pre>\n" + MIGRATE.HEADER + "</pre>\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "header|visible"):
            self.reviewed()
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.docs / MIGRATE.JOURNAL).exists())

    def test_html_after_comment_boundary_still_retains_example_content(self):
        for opening in ("<!-- example --> <pre>", "<!-- example\n--> <pre>"):
            with self.subTest(opening=opening):
                self.source(opening + "\n- Example finding.\n</pre>\n\n- Actual finding.\n")
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertEqual(plan["mappings"][0]["source"]["text"], "- Actual finding.")
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("Example finding", plan["unmapped"][0]["source"]["text"])

    def test_indented_source_lists_remain_visible_for_reconciliation(self):
        for indent in ("    ", "\t"):
            with self.subTest(indent=repr(indent)):
                self.source(indent + "- Example finding.\n\n- Actual finding.\n")
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("Example finding", plan["unmapped"][0]["source"]["text"])
                self.assert_refused(plan, "unmapped|disposition")

    def test_html_inside_fence_does_not_hide_following_live_content(self):
        self.source("```html\n<pre>\n- Example finding.\n```\n\n- Actual finding.\n")
        plan = self.reviewed()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(plan["unmapped"], [])
        self.assertIn("Actual finding", self.apply(plan))


if __name__ == "__main__":
    unittest.main()
