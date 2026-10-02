"""Fault-injection tests for the hardening acceptance gate.

These tests target the gate itself.  They ensure malformed child output and
false-green substitutions are rejected while a complete control is accepted.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import hashlib

from tests.acceptance_gate import GateError, validate_result


EXPECTED = {
    "doctor-mixed-list": {"outcome": "reject", "exit_code": 2,
                           "assertion": "wiring-block=FAIL"},
    "migration-split-terminator": {"outcome": "reject", "exit_code": 2,
                                    "assertion": "opaque-refusal-before-write"},
}
HASHES = {"scripts/docs-doctor.py": "doctor-sha",
          "scripts/docs-migrate.py": "migrate-sha"}


def control():
    return {"successful": True, "exit_code": 0, "tests": 2,
            "failures": [], "errors": [], "skips": [], "expected_failures": [],
            "runtime_hashes": dict(HASHES),
            "cases": [
                {"id": "doctor-mixed-list", "outcome": "reject", "exit_code": 2,
                 "assertion": "wiring-block=FAIL"},
                {"id": "migration-split-terminator", "outcome": "reject", "exit_code": 2,
                 "assertion": "opaque-refusal-before-write"},
            ]}


def canonical_control():
    manifest = json.loads((Path(__file__).parent /
                           "fixtures/hardening-2026-09-12/acceptance-cases.json").read_text())
    cases = [{"id": item["id"], "outcome": "reject" if item["exit"] else "accept",
              "exit_code": item["exit"], "assertion": item["assertion"]}
             for item in manifest["cases"]]
    return {"successful": True, "exit_code": 0, "tests": len(cases),
            "failures": [], "errors": [], "skips": [], "expected_failures": [],
            "runtime_hashes": dict(HASHES), "cases": cases}


class AcceptanceGateTests(unittest.TestCase):
    def assert_rejected(self, mutate):
        result = control()
        validate_result(result, EXPECTED, HASHES)
        mutate(result)
        with self.assertRaises(GateError):
            validate_result(result, EXPECTED, HASHES)

    def test_complete_control_is_accepted(self):
        validate_result(control(), EXPECTED, HASHES)

    def test_child_failures_errors_skips_and_expected_failures_rejected(self):
        for field in ("failures", "errors", "skips"):
            self.assert_rejected(lambda result, field=field: result[field].append({"id": "x"}))
        self.assert_rejected(lambda result: result.update(expected_failures=["x"]))

    def test_zero_discovery_and_nonzero_success_exit_rejected(self):
        self.assert_rejected(lambda result: result.update(tests=0))
        self.assert_rejected(lambda result: result.update(exit_code=1))
        self.assert_rejected(lambda result: result.pop("expected_failures"))
        with self.assertRaises(GateError):
            validate_result(control(), {}, HASHES)

    def test_failed_child_state_requires_nonzero_exit_and_diagnostic(self):
        result = control()
        result.update(successful=False, exit_code=0, failures=[{"message": "setup"}])
        with self.assertRaises(GateError):
            validate_result(result, EXPECTED, HASHES)
        result["exit_code"] = 1
        with self.assertRaises(GateError):
            validate_result(result, EXPECTED, HASHES)

    def test_case_manifest_is_complete_unique_and_behavioral(self):
        self.assert_rejected(lambda result: result["cases"].pop())
        self.assert_rejected(lambda result: result["cases"].append(copy.deepcopy(result["cases"][0])))
        self.assert_rejected(lambda result: result["cases"][0].update(assertion="no exception"))
        self.assert_rejected(lambda result: result["cases"][0].update(exit_code=0))
        with self.assertRaises(GateError):
            validate_result(control(), {"doctor-mixed-list": {}}, HASHES)

    def test_canonical_manifest_control_is_complete(self):
        manifest = json.loads((Path(__file__).parent /
                               "fixtures/hardening-2026-09-12/acceptance-cases.json").read_text())
        expected = {item["id"]: {"outcome": "reject" if item["exit"] else "accept",
                                  "exit_code": item["exit"],
                                  "assertion": item["assertion"]}
                    for item in manifest["cases"]}
        validate_result(canonical_control(), expected, HASHES)

    def test_canonical_corruptions_are_rejected(self):
        mutations = {
            "missing": lambda result: result["cases"].pop(),
            "duplicate": lambda result: result["cases"].append(copy.deepcopy(result["cases"][0])),
            "unexpected": lambda result: result["cases"].__setitem__(0, {
                "id": "unexpected", "outcome": "reject", "exit_code": 2,
                "assertion": "wiring-block=FAIL"}),
            "wrong outcome": lambda result: result["cases"][0].update(outcome="accept"),
            "wrong assertion": lambda result: result["cases"][0].update(assertion="wrong"),
            "wrong case exit": lambda result: result["cases"][0].update(exit_code=0),
            "nonzero aggregate exit": lambda result: result.update(exit_code=1),
            "inconsistent success": lambda result: result.update(successful=False),
            "failed child": lambda result: result["failures"].append({"id": "child"}),
            "expected failure": lambda result: result.update(expected_failures=["child"]),
            "hash mismatch": lambda result: result["runtime_hashes"].update({"scripts/docs-doctor.py": "wrong"}),
        }
        manifest = json.loads((Path(__file__).parent /
                               "fixtures/hardening-2026-09-12/acceptance-cases.json").read_text())
        expected = {item["id"]: {"outcome": "reject" if item["exit"] else "accept",
                                  "exit_code": item["exit"],
                                  "assertion": item["assertion"]}
                    for item in manifest["cases"]}
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                result = canonical_control()
                mutate(result)
                with self.assertRaises(GateError):
                    validate_result(result, expected, HASHES)

    def test_malformed_unknown_and_substituted_same_count_rejected(self):
        self.assert_rejected(lambda result: result.update(cases=[{"id": "substitute", "outcome": "pass", "exit_code": 0, "assertion": "ok"},
                                                                  {"id": "other", "outcome": "pass", "exit_code": 0, "assertion": "ok"}]))
        self.assert_rejected(lambda result: result.update(cases=[None, None]))
        self.assert_rejected(lambda result: result.update(runtime_hashes={"scripts/docs-doctor.py": "wrong", "scripts/docs-migrate.py": "migrate-sha"}))

    def test_frozen_acceptance_manifest_has_exact_sources_and_gate_fields(self):
        manifest = Path(__file__).parent / "fixtures/hardening-2026-09-12/acceptance-cases.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["version"], 1)
        self.assertIn("markdown-it-py 4.0.0", data["oracle"])
        self.assertIn("hand-authored", data["oracle"])
        cases = data["cases"]
        self.assertEqual(len(cases), 4)
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in cases:
            fixture = manifest.parent / case["fixture"]
            self.assertEqual(hashlib.sha256(fixture.read_bytes()).hexdigest(),
                             case["fixture_sha256"], case["id"])
            for field in ("classification", "inventory", "write", "exit", "positive", "scope", "assertion"):
                self.assertIn(field, case, case["id"])


if __name__ == "__main__":
    unittest.main()
