"""Doctor's --json mode, against text-mode baselines captured before it existed.

Each fixture project under fixtures/doctor-json/ is copied into a system
temporary directory, outside this repository's own register, so exits 0, 1
and 2 are asserted literally with no nested-register advisory. The baselines
in fixtures/doctor-json/baseline.json were captured with the Doctor at
6c96571; text mode must still reproduce them byte for byte. The one allowed
difference is the version number on the header line, so that a later version
bump does not force a recapture from the changed script.
"""
from pathlib import Path
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.test_doctor import load_doctor


ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "scripts/docs-doctor.py"
FIXTURES = ROOT / "tests/fixtures/doctor-json"
BASELINE = json.loads((FIXTURES / "baseline.json").read_text(encoding="utf-8"))
BASELINE_VERSION = "1.5.0"
TODAY = "2026-09-10"
KEYS = ["tool", "schema", "version", "root", "register_dir", "today", "checks", "summary", "exit_code", "error"]
LEVELS = ("PASS", "WARN", "FAIL", "INFO", "SKIP")
CHECK_ID_RE = re.compile(r"^[a-z]+(?:-[a-z]+)*$")
SUMMARY_RE = re.compile(r"^(\d+) checks: (\d+) pass, (\d+) warn, (\d+) fail, (\d+) info, (\d+) skipped — exit (\d+)$",
                        re.M)


def text_line(check):
    """The text-mode line a JSON check stands for."""
    return "%-4s  %-26s %s" % (check["level"], check["id"], check["message"])


def check_lines(stdout):
    return [line for line in stdout.splitlines() if line[:4] in LEVELS and line[4:6] == "  "]


class DoctorJsonTests(unittest.TestCase):
    doctor = load_doctor()

    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="doctor-json-")).resolve()
        self.addCleanup(shutil.rmtree, self.temp)

    def project(self, name):
        """A copy of fixture `name`, or an empty directory for a case with none."""
        target = self.temp / name
        if (FIXTURES / name).is_dir():
            shutil.copytree(FIXTURES / name, target)
        else:
            target.mkdir()
        return target

    def run_doctor(self, target, args, json_mode):
        argv = [sys.executable, "-B", str(DOCTOR), str(target)] + list(args) + (["--json"] if json_mode else [])
        process = subprocess.run(argv, capture_output=True, timeout=60)
        self.assertNotIn(b"Traceback", process.stderr, process.stderr)
        return process

    @staticmethod
    def snapshot(target):
        return {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob("*") if p.is_file()}

    def parse(self, process):
        """The one JSON object on stdout; nothing else may be there."""
        stdout = process.stdout
        self.assertTrue(stdout.isascii(), stdout)
        self.assertTrue(stdout.endswith(b"\n"), stdout)
        self.assertEqual(stdout.count(b"\n"), 1, "JSON mode printed more than one line:\n%r" % stdout)
        doc = json.loads(stdout.decode("ascii"))
        self.assertEqual(list(doc), KEYS)
        self.assertEqual(doc["tool"], "docs-doctor")
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["schema"], self.doctor.JSON_SCHEMA)
        self.assertEqual(doc["version"], self.doctor.VERSION)
        self.assertEqual(doc["exit_code"], process.returncode)
        if process.returncode == 3:
            self.assertIsInstance(doc["error"], str)
            self.assertEqual("docs-doctor: %s\n" % doc["error"], process.stderr.decode("utf-8"))
        else:
            self.assertIsNone(doc["error"])
        self.assertIsInstance(doc["checks"], list)
        for check in doc["checks"]:
            self.assertEqual(list(check), ["id", "level", "message"])
            self.assertIn(check["level"], LEVELS)
            self.assertRegex(check["id"], CHECK_ID_RE)
            self.assertIsInstance(check["message"], str)
        self.assertEqual(list(doc["summary"]), [level.lower() for level in LEVELS])
        self.assertEqual(doc["summary"], {level.lower(): sum(c["level"] == level for c in doc["checks"])
                                          for level in LEVELS})
        return doc

    def test_text_mode_matches_the_captured_baseline(self):
        for name, case in BASELINE["cases"].items():
            with self.subTest(case=name):
                expected = (FIXTURES / case["stdout"]).read_bytes()
                self.assertEqual(hashlib.sha256(expected).hexdigest(), case["stdout_sha256"])
                header = "docs-doctor %s — " % BASELINE_VERSION
                if expected:
                    self.assertTrue(expected.decode("utf-8").startswith(header), expected[:80])
                    expected = expected.replace(header.encode("utf-8"),
                                                ("docs-doctor %s — " % self.doctor.VERSION).encode("utf-8"), 1)
                target = self.project(name)
                before = self.snapshot(target)
                process = self.run_doctor(target, case["args"], json_mode=False)
                self.assertEqual(process.stdout, expected)
                self.assertEqual(process.stderr.decode("utf-8"), case["stderr"])
                self.assertEqual(process.returncode, case["exit"])
                self.assertEqual(self.snapshot(target), before, "Doctor modified its input project")

    def test_json_mode_reports_the_same_checks_summary_and_exit_as_text_mode(self):
        expected_complaints = {"pass": {}, "warn": {"readme-footer": "WARN"}, "fail": {"decisions-ids": "FAIL"}}
        for name, complaints in expected_complaints.items():
            with self.subTest(case=name):
                case = BASELINE["cases"][name]
                target = self.project(name)
                before = self.snapshot(target)
                text = self.run_doctor(target, case["args"], json_mode=False)
                emitted = self.run_doctor(target, case["args"], json_mode=True)
                self.assertEqual(self.snapshot(target), before, "Doctor modified its input project")
                doc = self.parse(emitted)

                self.assertEqual(emitted.returncode, case["exit"])
                self.assertEqual(text.returncode, case["exit"])
                self.assertEqual(emitted.stderr, b"")
                self.assertEqual(emitted.stderr, text.stderr)
                self.assertEqual(doc["root"], str(target))
                self.assertEqual(doc["register_dir"], str(target / "docs"))
                self.assertEqual(doc["today"], TODAY)

                stdout = text.stdout.decode("utf-8")
                self.assertEqual([text_line(c) for c in doc["checks"]], check_lines(stdout))
                ids = [c["id"] for c in doc["checks"]]
                self.assertEqual(len(ids), len(set(ids)), "a check id repeated within one run")
                total, passed, warned, failed, info, skipped, code = map(int, SUMMARY_RE.search(stdout).groups())
                self.assertEqual(total, len(doc["checks"]))
                self.assertEqual(doc["summary"], {"pass": passed, "warn": warned, "fail": failed,
                                                  "info": info, "skip": skipped})
                self.assertEqual(doc["exit_code"], code)
                self.assertEqual({c["id"]: c["level"] for c in doc["checks"] if c["level"] in ("WARN", "FAIL")},
                                 complaints)

    def test_runs_that_cannot_start_still_print_one_object(self):
        missing = self.temp / "no-such-directory"
        cases = {
            "no-register": (self.project("no-register"), BASELINE["cases"]["no-register"]["args"], TODAY),
            "bad-today": (self.project("bad-today"), BASELINE["cases"]["bad-today"]["args"], None),
            "not-a-directory": (missing, ["--today", TODAY, "--no-git"], TODAY),
        }
        for name, (target, args, today) in cases.items():
            with self.subTest(case=name):
                text = self.run_doctor(target, args, json_mode=False)
                emitted = self.run_doctor(target, args, json_mode=True)
                doc = self.parse(emitted)
                self.assertEqual(text.returncode, 3)
                self.assertEqual(text.stdout, b"")
                self.assertEqual(emitted.returncode, 3)
                self.assertEqual(emitted.stderr, text.stderr)
                self.assertTrue(emitted.stderr.startswith(b"docs-doctor: "), emitted.stderr)
                self.assertEqual(doc["root"], os.path.realpath(str(target)))
                self.assertIsNone(doc["register_dir"])
                self.assertEqual(doc["today"], today)
                self.assertEqual(doc["checks"], [])
                self.assertEqual(sum(doc["summary"].values()), 0)
                self.assertTrue(doc["error"])

    def test_a_docs_directory_argument_reports_its_parent_as_root(self):
        target = self.project("pass")
        args = BASELINE["cases"]["pass"]["args"]
        text = self.run_doctor(target / "docs", args, json_mode=False)
        doc = self.parse(self.run_doctor(target / "docs", args, json_mode=True))
        self.assertIn("treating its parent as the project root", text.stdout.decode("utf-8"))
        self.assertEqual(doc["root"], str(target))
        self.assertEqual(doc["register_dir"], str(target / "docs"))
        self.assertEqual([text_line(c) for c in doc["checks"]], check_lines(text.stdout.decode("utf-8")))
        self.assertEqual(doc["exit_code"], text.returncode)

    def test_a_crash_mid_run_keeps_the_checks_already_made_and_exits_three(self):
        target = self.project("pass")
        args = [str(target)] + BASELINE["cases"]["pass"]["args"]
        outputs = {}
        for json_mode in (False, True):
            doctor = load_doctor()

            def crash(*_args, **_kwargs):
                raise RuntimeError("injected")

            doctor.check_status = crash
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = doctor.main(args + (["--json"] if json_mode else []))
            self.assertEqual(code, 3)
            self.assertEqual(stderr.getvalue(), "docs-doctor: checker error: RuntimeError: injected\n")
            outputs[json_mode] = stdout.getvalue()
        doc = json.loads(outputs[True])
        self.assertEqual(outputs[True].count("\n"), 1)
        self.assertEqual(doc["exit_code"], 3)
        self.assertEqual(doc["error"], "checker error: RuntimeError: injected")
        self.assertEqual([c["id"] for c in doc["checks"]][-1], "changelog-decision-refs")
        self.assertNotIn("status-size", [c["id"] for c in doc["checks"]])
        self.assertEqual([text_line(c) for c in doc["checks"]], check_lines(outputs[False]))
        self.assertEqual(sum(doc["summary"].values()), len(doc["checks"]))
        self.assertIsNone(SUMMARY_RE.search(outputs[False]), "text mode printed a summary after a crash")


if __name__ == "__main__":
    unittest.main()
