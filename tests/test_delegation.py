"""Delegation clause currency and advisory git capability boundaries."""
import unittest
from unittest.mock import patch

from tests.test_doctor import ROOT, WIRING, install_wiring_block, load_doctor


class DelegationTests(unittest.TestCase):
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
