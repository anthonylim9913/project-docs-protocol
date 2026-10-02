"""Regression cases for declaration, PI, and CDATA migration boundaries."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/docs-migrate.py"
SPEC = importlib.util.spec_from_file_location("migrate_opaque", SCRIPT)
MIGRATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATE)
TODAY = "2026-09-12"


class OpaqueMigrationTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / "tests/.tmp"
        scratch.mkdir(exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix="opaque-migration-", dir=scratch))
        self.addCleanup(shutil.rmtree, self.root)
        self.docs = self.root / "docs"
        self.docs.mkdir()
        (self.docs / "CHANGELOG.md").write_text("# CHANGELOG\n")
        (self.docs / "DECISIONS.md").write_text("# DECISIONS\n")

    def status(self, body):
        (self.docs / "STATUS.md").write_text("# STATUS\n\n## In flight\n\n" + body)

    def reviewed(self, plan=None):
        plan = plan or MIGRATE.build_plan(self.docs, TODAY)
        for mapping in plan["mappings"]:
            mapping["reviewed"] = True
            mapping["row"]["closes_when"] = "Opaque boundary fixture passes."
        return plan

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.docs.iterdir() if p.is_file()}

    def test_special_blocks_are_single_unresolved_records_and_adjacent_content_maps(self):
        cases = {
            "cdata": ("<![CDATA[", "]]>"),
            "declaration": ("<!DOCTYPE fixture [", "]>"),
            "processing_instruction": ("<?fixture", "?>"),
        }
        for name, (opening, closing) in cases.items():
            with self.subTest(name=name):
                source = f"{opening}\n| Item | Notes |\n|---|---|\n| Example parser | hidden |\n{closing}\n\n- Actual finding.\n"
                self.status(source)
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertEqual(plan["mappings"][0]["source"]["text"], "- Actual finding.")
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertEqual(plan["unmapped"][0]["source"]["text"], source.rstrip("\n").rsplit("\n\n", 1)[0])

    def test_incomplete_special_blocks_at_eof_are_preserved_and_refused_before_write(self):
        for name, opening in (("cdata", "<![CDATA["), ("declaration", "<!DOCTYPE fixture ["), ("pi", "<?fixture")):
            with self.subTest(name=name):
                source = f"{opening}\n| Item | Notes |\n|---|---|\n| Example parser | hidden |\n"
                self.status(source)
                plan = self.reviewed()
                self.assertEqual(plan["mappings"], [])
                self.assertEqual(len(plan["unmapped"]), 1)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "unmapped|disposition"):
                    MIGRATE.validate_plan(self.docs, plan, TODAY)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.docs / MIGRATE.JOURNAL).exists())

    def test_special_terminators_ignore_inner_gt_and_quoted_gt(self):
        cases = {
            "processing_instruction": ("<?fixture payload > remains", "?>"),
            "declaration": ('<!DOCTYPE fixture "quoted > value" [', "]>"),
        }
        for name, (opening, closing) in cases.items():
            with self.subTest(name=name):
                self.status(f"{opening}\ninner > delimiter-looking text\n{closing}\n\n- Actual finding.\n")
                plan = self.reviewed()
                self.assertEqual(len(plan["mappings"]), 1)
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("inner > delimiter-looking text", plan["unmapped"][0]["source"]["text"])

    def test_split_cdata_and_pi_terminators_do_not_cross_physical_newlines(self):
        # A delimiter is a literal contiguous token. A newline between its
        # characters leaves the opaque block unresolved through EOF, so inner
        # headings/findings cannot become live records.
        for opening, split, closing in (("<![CDATA[", "]]", ">"),
                                        ("<?fixture", "?", ">")):
            with self.subTest(opening=opening):
                self.status(f"{opening}\nexample\n{split}\n{closing}\n\n- Actual finding.\n")
                plan = self.reviewed()
                self.assertEqual(plan["mappings"], [])
                self.assertEqual(len(plan["unmapped"]), 1)
                self.assertIn("- Actual finding.", plan["unmapped"][0]["source"]["text"])

    def test_declaration_subset_terminator_remains_bounded_across_lines(self):
        self.status("<!DOCTYPE fixture [\nexample\n]\n>\n\n- Actual finding.\n")
        plan = self.reviewed()
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(plan["mappings"][0]["source"]["text"], "- Actual finding.")
        self.assertEqual(len(plan["unmapped"]), 1)

    def test_multiple_physical_split_blocks_do_not_expose_inner_findings(self):
        source = ("<![CDATA[\n]]\n>\n## Findings\n\n- Hidden\n"
                  "and PI <?audit\n?\n>\n")
        self.status(source)
        plan = self.reviewed()
        self.assertEqual(plan["mappings"], [])
        self.assertEqual(len(plan["unmapped"]), 1)
        self.assertIn("## Findings", plan["unmapped"][0]["source"]["text"])
        self.assertIn("- Hidden", plan["unmapped"][0]["source"]["text"])

    def test_context_disposition_preserves_source_without_phantom_records(self):
        source = "<![CDATA[\n## Findings\n- Example parser\n]]>\n"
        self.status(source)
        status_before = (self.docs / "STATUS.md").read_bytes()
        plan = self.reviewed()
        plan["unmapped"][0].update(disposition="context", reason="Illustrative payload, no live finding.")
        MIGRATE.apply_plan(self.docs, plan, TODAY)
        self.assertEqual(status_before, (self.docs / "STATUS.md").read_bytes())
        self.assertNotIn("Example parser", (self.docs / "LEDGER.md").read_text())
        changelog = (self.docs / "CHANGELOG.md").read_text()
        self.assertIn("Illustrative payload", changelog)
        self.assertNotIn("\n## Findings\n", changelog)

    def test_hidden_special_ledger_table_is_refused_without_mutation(self):
        header = MIGRATE.HEADER
        for name, block in (("cdata", f"<![CDATA[\n{header}]]>\n"),
                            ("declaration", f"<!DOCTYPE fixture [\n{header}]>\n"),
                            ("pi", f"<?fixture\n{header}?>\n")):
            with self.subTest(name=name):
                self.status("- Actual finding.\n")
                (self.docs / "LEDGER.md").write_text(block)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "header|visible"):
                    MIGRATE.build_plan(self.docs, TODAY)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.docs / MIGRATE.JOURNAL).exists())

    def test_hidden_split_cdata_and_pi_ledger_tables_are_refused(self):
        # A ten-column ledger header hidden by an unterminated physical
        # delimiter split must not become the write target.
        header = MIGRATE.HEADER
        for name, block in (("cdata", f"<![CDATA[\n{header}\n]]\n>\n"),
                            ("pi", f"<?fixture\n{header}\n?\n>\n")):
            with self.subTest(name=name):
                self.status("- Actual finding.\n")
                (self.docs / "LEDGER.md").write_text(block)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "header|visible"):
                    MIGRATE.build_plan(self.docs, TODAY)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.docs / MIGRATE.JOURNAL).exists())

    def test_exact_cdata_status_never_invents_blocked_row_and_real_table_remains_usable(self):
        source = ("<![CDATA[\n"
                  "| Item | Status | Gate |\n"
                  "|---|---|---|\n"
                  "| Illustrative parser | BLOCKED | owner |\n"
                  "]]>")
        self.status(source + "\n\n| Item | Status | Gate |\n|---|---|---|\n| Real parser | OPEN | |\n")
        status_before = (self.docs / "STATUS.md").read_bytes()
        plan = MIGRATE.build_plan(self.docs, TODAY)
        self.assertEqual(len(plan["mappings"]), 1)
        self.assertEqual(plan["mappings"][0]["source"]["text"], "| Real parser | OPEN | |")
        self.assertEqual(len(plan["unmapped"]), 1)
        self.assertIn("Illustrative parser", plan["unmapped"][0]["source"]["text"])
        plan["unmapped"][0].update(disposition="context", reason="CDATA example retained for reconciliation.")
        plan["mappings"][0]["reviewed"] = True
        plan["mappings"][0]["row"]["closes_when"] = "Real parser acceptance is verified."
        MIGRATE.apply_plan(self.docs, plan, TODAY)
        self.assertEqual(status_before, (self.docs / "STATUS.md").read_bytes())
        ledger = (self.docs / "LEDGER.md").read_text()
        self.assertIn("Real parser", ledger)
        self.assertNotIn("Illustrative parser", ledger)
        self.assertIn("CDATA example retained", (self.docs / "CHANGELOG.md").read_text())


if __name__ == "__main__":
    unittest.main()
