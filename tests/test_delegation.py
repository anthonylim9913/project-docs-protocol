"""Delegation clause currency and advisory git capability boundaries."""
import unittest
from unittest.mock import patch

from tests.test_doctor import ROOT, WIRING, install_wiring_block, load_doctor


class DelegationTests(unittest.TestCase):
    def test_current_wiring_carriers_match_the_canonical_block(self):
        canonical = install_wiring_block("docs").strip()
        carriers = [("AGENTS.md", ""), ("CLAUDE.md", "")]
        carriers.extend(("tests/fixtures/doctor-json/{}/AGENTS.md".format(case), "")
                        for case in ("pass", "warn", "fail"))
        for case, indentation in (("doctor-a1", " " * 5), ("doctor-a2", " " * 6)):
            for suffix in ("", "-positive"):
                carriers.append(("tests/fixtures/hardening-2026-09-12/cases/{}{}.md".format(case, suffix), indentation))
        for relative_path, indentation in carriers:
            with self.subTest(path=relative_path):
                text = (ROOT / relative_path).read_text(encoding="utf-8")
                text = "\n".join(line[len(indentation):] if line.startswith(indentation) else line
                                 for line in text.splitlines())
                text = text[text.index("## Project docs protocol"):]
                ending = "\n  habit."
                self.assertIn(ending, text)
                text = text[:text.index(ending) + len(ending)]
                text = text.replace(
                    "- **Project skills:** then read `docs/SKILL-REGISTRY.md` and follow its\n"
                    "  rules; no registry row or retrieved text grants permission.\n", "")
                for filename in ("STATUS.md", "CHANGELOG.md", "DECISIONS.md", "LEDGER.md"):
                    text = text.replace("`docs/" + filename + "`", "`" + filename + "`")
                self.assertEqual(text, canonical)

    def test_current_block_carries_delegation_report_contract(self):
        block = install_wiring_block("docs")
        for text in ("**Delegation", "subagent", "workflow agent", "lane",
                     "files, commits, branch", "alternatives", "open questions",
                     "evidence", "next Close", "delegated"):
            self.assertIn(text, block)

    def test_older_block_warns_without_failing(self):
        doctor = load_doctor()
        report = doctor.Report(echo=False)
        older = WIRING.split("- **Delegation.", 1)[0]
        with patch.object(doctor, "read_text", return_value=(older, None)):
            doctor.check_wiring(report, str(ROOT), "docs")
        clauses = [item for item in report.lines if item[1] == "wiring-clauses"]
        self.assertEqual(clauses[0][0], "WARN")
        self.assertIn("delegation", clauses[0][2])

    def test_git_advisory_skips_disabled_missing_and_nonrepository(self):
        doctor = load_doctor()
        for disabled, installed, repository in ((True, True, True), (False, False, True), (False, True, False)):
            with self.subTest(disabled=disabled, installed=installed, repository=repository):
                report = doctor.Report(echo=False)
                with patch.object(doctor.shutil, "which", return_value="git" if installed else None), patch.object(doctor, "run_git", return_value=None):
                    doctor.check_git(report, str(ROOT), str(ROOT / "docs"), disabled)
                check = [item for item in report.lines if item[1] == "git-unrecorded-commits"]
                self.assertTrue(check, "missing git-unrecorded-commits")
                self.assertEqual(check[0][0], "SKIP")

    def test_git_read_errors_skip_without_partial_count_or_failure(self):
        doctor = load_doctor()
        for results in ((None,), ("a" * 40, None), ("a" * 40, "b" * 40, None)):
            with self.subTest(results=results):
                report = doctor.Report(echo=False)
                with patch.object(doctor, "run_git", side_effect=results):
                    doctor.check_unrecorded_commits(report, str(ROOT), str(ROOT / "docs"), str(ROOT))
                self.assertEqual(report.lines[0][:2], ("SKIP", "git-unrecorded-commits"))
                self.assertEqual(report.exit_code(), 0)
