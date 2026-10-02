"""Replay retained lifecycle examples through the real, read-only Doctor.

The JSON traces are authored protocol examples, not output from an automatic
Brief/Close writer: no such writer ships. Replaying their exact bytes proves
that Doctor diagnoses the interrupted states and that these examples preserve
their stated identity/provenance contracts. It does not prove that an arbitrary
agent follows the protocol. Independent agent exercises are separate evidence.
"""

from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "lifecycle"
DOCTOR = ROOT / "scripts" / "docs-doctor.py"
TODAY = "2026-09-10"


class LifecycleReplayTests(unittest.TestCase):
    """Structural fixture oracles plus executable Doctor integration checks."""

    def setUp(self):
        scratch = ROOT / "tests" / ".tmp"
        scratch.mkdir(exist_ok=True)
        self.project = Path(tempfile.mkdtemp(prefix="lifecycle-", dir=scratch))
        self.addCleanup(shutil.rmtree, self.project)
        # Active wiring is shared with the installed repository under test.
        shutil.copyfile(ROOT / "AGENTS.md", self.project / "AGENTS.md")
        self.write_files(json.loads((FIXTURES / "base.json").read_text()))

    def write_files(self, files):
        """Apply recorded bytes; deliberately contains no lifecycle decisions."""
        for relative, content in files.items():
            destination = self.project / relative
            self.assertTrue(destination.resolve().is_relative_to(self.project))
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")

    def load_trace(self, name):
        trace = json.loads((FIXTURES / f"{name}.json").read_text())
        self.write_files(trace["before"])
        return trace

    def apply_step(self, trace, name):
        step, = [step for step in trace["steps"] if step["name"] == name]
        self.write_files(step["writes"])
        return step

    def contents(self, relative):
        return (self.project / relative).read_text(encoding="utf-8")

    def snapshot(self):
        return {str(p.relative_to(self.project)): p.read_bytes()
                for p in self.project.rglob("*") if p.is_file()}

    def doctor(self, expected_exit, **expected_levels):
        before = self.snapshot()
        result = subprocess.run(
            [sys.executable, "-B", str(DOCTOR), str(self.project),
             "--today", TODAY, "--no-git"],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.stderr, "", result.stderr)
        self.assertEqual(result.returncode, expected_exit, result.stdout)
        levels = dict((check, level) for level, check in
                      re.findall(r"^(PASS|WARN|FAIL|INFO|SKIP)\s+(\S+)",
                                 result.stdout, re.MULTILINE))
        # The user requires scratch projects inside this repository. Doctor
        # correctly sees its ancestor register and reports this known advisory.
        self.assertEqual(levels.get("nested-register"), "WARN", result.stdout)
        for check, level in expected_levels.items():
            self.assertEqual(levels.get(check.replace("_", "-")), level,
                             result.stdout)
        expected_problems = {"nested-register": "WARN"}
        expected_problems.update({check.replace("_", "-"): level
                                  for check, level in expected_levels.items()
                                  if level in ("WARN", "FAIL")})
        actual_problems = {check: level for check, level in levels.items()
                           if level in ("WARN", "FAIL")}
        self.assertEqual(actual_problems, expected_problems, result.stdout)
        self.assertEqual(before, self.snapshot(), "Doctor changed project files")
        return result.stdout

    def row(self, relative, identifier):
        # Fixtures intentionally have unescaped cells; production parsing is
        # exercised independently by invoking Doctor, never reproduced here.
        rows = [line for line in self.contents(relative).splitlines()
                if line.startswith(f"| {identifier} |")]
        self.assertEqual(len(rows), 1, (relative, identifier, rows))
        return rows[0], [cell.strip() for cell in rows[0].split("|")[1:-1]]

    def decision_ids(self):
        return re.findall(r"^## (D-\d+)\b", self.contents("docs/DECISIONS.md"),
                          re.MULTILINE)

    def test_brief_one_option_authorized_recorded_artifact(self):
        trace = self.load_trace("brief-authorized")
        self.assertIn("You may normalize the local sample now", trace["owner"])
        self.doctor(1)
        for step in trace["steps"]:
            self.apply_step(trace, step["name"])
        self.assertEqual(self.contents("artifacts/sample.txt"), "alpha\nbeta\n")
        self.assertEqual(self.decision_ids(), [])
        self.assertIn("delegated authority", self.contents("docs/CHANGELOG.md"))
        self.doctor(1, ledger_schema="PASS")

    def test_brief_one_option_owner_gate_survives_silence(self):
        trace = self.load_trace("brief-gated")
        original_status = self.contents("docs/STATUS.md")
        original_ledger = self.contents("docs/LEDGER.md")
        self.assertEqual(trace["owner"], "No answer received.")
        for step in trace["steps"]:
            self.apply_step(trace, step["name"])
        self.assertEqual(self.contents("docs/STATUS.md"), original_status)
        self.assertEqual(self.contents("docs/LEDGER.md"), original_ledger)
        self.assertFalse((self.project / "artifacts/execution.txt").exists())
        self.assertEqual(self.decision_ids(), [])
        self.assertIn("Q1 — not answered", self.contents("docs/CHANGELOG.md"))
        self.doctor(1, ledger_blocked_on="PASS")

    def test_brief_method_approval_does_not_authorize_execution(self):
        trace = self.load_trace("brief-method-only")
        original_status = self.contents("docs/STATUS.md")
        original_ledger = self.contents("docs/LEDGER.md")
        self.assertIn("do not execute it yet", trace["owner"])
        for step in trace["steps"]:
            self.apply_step(trace, step["name"])
        self.assertEqual(self.contents("docs/STATUS.md"), original_status)
        self.assertEqual(self.contents("docs/LEDGER.md"), original_ledger)
        self.assertFalse((self.project / "artifacts/execution.txt").exists())
        self.assertEqual(self.decision_ids(), [])
        self.doctor(1, ledger_blocked_on="PASS")

    def test_brief_mixed_answers_default_partial_gate_and_terminal_ruling(self):
        trace = self.load_trace("brief-mixed")
        original_questions = self.contents("docs/STATUS.md").splitlines()
        unanswered = [line for line in original_questions
                      if re.match(r"[345]\. ", line)]
        original_rows = {key: self.row("docs/LEDGER.md", key)[0]
                         for key in ("LG-0003", "LG-0004", "LG-0005")}
        self.doctor(1)
        self.apply_step(trace, "log-answers-and-reservation")
        self.doctor(1, changelog_decision_refs="WARN")
        self.apply_step(trace, "record-owner-decision")
        self.doctor(1, changelog_decision_refs="INFO")
        # Archive written first while the original live row still exists.
        self.apply_step(trace, "archive-terminal-ruling")
        self.doctor(2, ledger_archive_ids="FAIL")
        self.apply_step(trace, "update-live-ledger")
        self.apply_step(trace, "rewrite-dashboard")
        self.doctor(1, ledger_schema="PASS", ledger_archive_ids="PASS")
        status = self.contents("docs/STATUS.md")
        for question in unanswered:
            self.assertIn(question, status.splitlines())
        for key, row in original_rows.items():
            self.assertEqual(self.row("docs/LEDGER.md", key)[0], row)
        self.assertNotRegex(status, r"(?m)^[12]\. ")
        self.assertEqual(self.decision_ids(), ["D-0001"])
        _, partial = self.row("docs/LEDGER.md", "LG-0002")
        self.assertEqual(partial[2], "BLOCKED")
        self.assertEqual(partial[7], "LG-0006; external storage review")
        self.assertIn("Brief 2026-09-10 Q2: default, no decision entry", partial[9])
        self.assertNotRegex(partial[9], r"\bD-\d+")
        _, terminal = self.row("docs/LEDGER-ARCHIVE.md", "LG-0001")
        self.assertEqual(terminal[2], "NOT-AN-ISSUE")
        self.assertIn("D-0001", terminal[9])
        self.assertIn("Withdraw the duplicate", terminal[9])
        log = self.contents("docs/CHANGELOG.md")
        self.assertEqual(log.count("— brief:"), 1)
        for number in (3, 4, 5):
            self.assertIn(f"Q{number} — not answered", log)

    def test_interrupted_reservation_intervening_close_and_recovery(self):
        trace = self.load_trace("interrupted-brief")
        self.doctor(1)
        self.apply_step(trace, "reserve-brief-decisions")
        reserved_log = self.contents("docs/CHANGELOG.md")
        self.assertIn("Reserved decisions: D-0002–D-0003", reserved_log)
        self.doctor(1, changelog_decision_refs="WARN")
        self.apply_step(trace, "intervening-close-log")
        self.apply_step(trace, "intervening-close-dashboard")
        self.apply_step(trace, "intervening-close-decision")
        intervening_decision = self.contents("docs/DECISIONS.md")
        self.assertEqual(self.decision_ids(), ["D-0001", "D-0004"])
        output = self.doctor(1, changelog_decision_refs="WARN")
        self.assertIn("D-0002", output)
        self.assertIn("D-0003", output)
        self.apply_step(trace, "recover-first-reserved-decision")
        output = self.doctor(1, changelog_decision_refs="WARN", decisions_order="WARN")
        ref_line = next(line for line in output.splitlines()
                        if "changelog-decision-refs" in line)
        self.assertIn("D-0003", ref_line)
        self.assertNotIn("missing D-0002", ref_line)
        self.apply_step(trace, "recover-second-reserved-decision")
        self.apply_step(trace, "recover-dashboard")
        self.assertEqual(self.decision_ids(), ["D-0001", "D-0004", "D-0002", "D-0003"])
        self.assertTrue(self.contents("docs/DECISIONS.md").startswith(intervening_decision))
        self.assertIn(reserved_log.removeprefix("# CHANGELOG\n\n"),
                      self.contents("docs/CHANGELOG.md"))
        # Repeated read-only reconciliation finds no missing IDs and changes no
        # bytes. This does not claim to test an automatic recovery writer.
        before = self.snapshot()
        self.doctor(1, changelog_decision_refs="INFO", decisions_order="WARN")
        self.doctor(1, changelog_decision_refs="INFO", decisions_order="WARN")
        self.assertEqual(before, self.snapshot())

    def test_reserved_id_semantic_conflict_is_manual_boundary(self):
        trace = self.load_trace("interrupted-brief")
        self.apply_step(trace, "reserve-brief-decisions")
        self.apply_step(trace, "conflicting-decisions")
        original = self.snapshot()
        # Existing IDs resolve even when their meaning disagrees with the
        # Brief: the checker must not be credited with semantic reconciliation.
        self.doctor(1, changelog_decision_refs="INFO")
        self.assertIn("Unrelated retention choice", self.contents("docs/DECISIONS.md"))
        self.assertIn("regional storage", self.contents("docs/CHANGELOG.md"))
        self.assertEqual(original, self.snapshot())

    def test_archive_first_replay_preserves_exact_row_and_conflict(self):
        trace = self.load_trace("archive-reopen")
        self.apply_step(trace, "close-log")
        self.apply_step(trace, "terminal-live-row")
        exact_row, _ = self.row("docs/LEDGER.md", "LG-0001")
        self.doctor(2, ledger_terminal_leak="FAIL", ledger_evidence="PASS")
        self.apply_step(trace, "archive-copy")
        self.assertEqual(self.row("docs/LEDGER-ARCHIVE.md", "LG-0001")[0], exact_row)
        self.doctor(2, ledger_archive_ids="FAIL", ledger_terminal_leak="FAIL")
        before = self.snapshot()
        self.doctor(2, ledger_archive_ids="FAIL", ledger_terminal_leak="FAIL")
        self.assertEqual(before, self.snapshot())
        self.apply_step(trace, "remove-live-row")
        self.apply_step(trace, "close-dashboard")
        self.doctor(1, ledger_archive_ids="PASS")
        self.assertEqual(self.contents("docs/LEDGER-ARCHIVE.md").count(exact_row), 1)
        # Restore an intentionally conflicting copy: Doctor detects identity
        # overlap, but exact cell conflict is assessed by the fixture oracle.
        self.apply_step(trace, "conflicting-live-copy")
        self.assertNotEqual(self.row("docs/LEDGER.md", "LG-0001")[0], exact_row)
        conflict = self.snapshot()
        self.doctor(2, ledger_archive_ids="FAIL")
        self.assertEqual(conflict, self.snapshot())

    def test_reopen_marker_identifies_row_and_exact_archive_event(self):
        trace = self.load_trace("archive-reopen")
        for name in ("close-log", "terminal-live-row", "archive-copy",
                     "remove-live-row", "close-dashboard", "reopen-log",
                     "append-reopen-marker", "restore-original-id"):
            self.apply_step(trace, name)
        archived_row, _ = self.row("docs/LEDGER-ARCHIVE.md", "LG-0001")
        archived_hash = sha256(archived_row.encode("utf-8")).hexdigest()
        self.assertIn(f"REOPENED 2026-09-10 LG-0001 archive-sha256:{archived_hash} → live",
                      self.contents("docs/LEDGER-ARCHIVE.md"))
        _, reopened = self.row("docs/LEDGER.md", "LG-0001")
        self.assertEqual(reopened[2], "OPEN")
        self.assertIn(archived_hash, reopened[9])
        self.assertNotIn("LG-0002", self.contents("docs/LEDGER.md"))
        # Deliberately conservative: Doctor does not validate reopen events.
        self.doctor(2, ledger_archive_ids="FAIL", ledger_schema="PASS")

    def test_non_git_durable_evidence_matches_artifact_and_command(self):
        trace = self.load_trace("archive-reopen")
        self.apply_step(trace, "close-log")
        self.apply_step(trace, "terminal-live-row")
        _, row = self.row("docs/LEDGER.md", "LG-0001")
        evidence = row[9]
        digest, = re.findall(r"sha256:([0-9a-f]{64})", evidence)
        artifact = self.project / "artifacts/result.txt"
        self.assertEqual(sha256(artifact.read_bytes()).hexdigest(), digest)
        result = subprocess.run(
            [sys.executable, "-B", "checks/verify_result.py"], cwd=self.project,
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual((result.returncode, result.stdout, result.stderr),
                         (0, "PASS: result is stable\n", ""))
        self.doctor(2, ledger_evidence="PASS", ledger_terminal_leak="FAIL")
        artifact.write_text("wrong result\n", encoding="utf-8")
        failed = subprocess.run(
            [sys.executable, "-B", "checks/verify_result.py"], cwd=self.project,
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(failed.returncode, 1)
        self.assertNotEqual(sha256(artifact.read_bytes()).hexdigest(), digest)
        # Doctor validates evidence shape, not artifact contents; the separate
        # real command and hash comparison above supply that evidence here.
        self.doctor(2, ledger_evidence="PASS", ledger_terminal_leak="FAIL")


if __name__ == "__main__":
    unittest.main()
