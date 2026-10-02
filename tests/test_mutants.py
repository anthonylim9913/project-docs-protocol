"""Canonical acceptance controls for semantic Doctor and migration mutants."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.run_acceptance import runtime_hashes
from tests.acceptance_support import copy_subject, commit


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests/run_acceptance.py"
MANIFEST = ROOT / "tests/fixtures/hardening-2026-09-12/acceptance-cases.json"
VALIDATOR = ROOT / "tests/validate_acceptance.py"


class MutantSensitivityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="acceptance-mutants-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def runtime_copy(self, name):
        runtime = self.root / name
        copy_subject(runtime)
        process, result_path, _ = self.run_acceptance(runtime)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(self.validate(result_path, runtime).returncode, 0)
        return runtime

    def run_acceptance(self, runtime):
        result = self.root / f"{runtime.name}.result.json"
        process = subprocess.run(
            [sys.executable, "-B", str(runtime / "tests/run_acceptance.py"), "--runtime-root", str(runtime),
             "--result", str(result), "--source-commit", subprocess.run(
                 ["git", "rev-parse", "HEAD"], cwd=runtime, check=True,
                 capture_output=True, text=True).stdout.strip()],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        self.assertTrue(result.is_file(), process.stdout + process.stderr)
        return process, result, json.loads(result.read_text(encoding="utf-8"))

    @staticmethod
    def source_commit():
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def validate(self, result_path, runtime):
        hashes = self.root / f"{runtime.name}.hashes.json"
        values = runtime_hashes(runtime)
        hashes.write_text(json.dumps(values, sort_keys=True), encoding="utf-8")
        return subprocess.run(
            [sys.executable, "-B", str(runtime / "tests/validate_acceptance.py"), str(result_path),
             str(runtime / "tests/fixtures/hardening-2026-09-12/acceptance-cases.json"), str(hashes)],
            cwd=ROOT, capture_output=True, text=True, timeout=15,
        )

    def test_unmutated_runtime_is_accepted_by_canonical_bundle(self):
        runtime = self.runtime_copy("control")
        commit(runtime)
        process, result_path, payload = self.run_acceptance(runtime)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        validator = self.validate(result_path, runtime)
        self.assertEqual(validator.returncode, 0, validator.stdout + validator.stderr)
        self.assertEqual(payload["source_commit"], subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=runtime, check=True,
            capture_output=True, text=True).stdout.strip())
        self.assertEqual({case["id"] for case in payload["cases"]}, {
            "doctor-a1", "doctor-a2", "migration-split-cdata", "migration-split-pi",
        })
        self.assertTrue(all(case["outcome"] == "reject" for case in payload["cases"]))
        self.assertTrue(all(case["protected_state"]["unchanged"] for case in payload["cases"]))
        self.assertTrue(all(case["positive_control"]["passed"] for case in payload["cases"]))
        self.assertTrue(all(case["stages"] for case in payload["cases"]))

    def test_doctor_mutant_is_rejected_by_canonical_acceptance_contract(self):
        runtime = self.runtime_copy("doctor-mutant")
        path = runtime / "scripts/docs-doctor.py"
        text = path.read_text(encoding="utf-8")
        self.assertIn("root_transition = bool(stack) and matched == 0", text)
        path.write_text(text.replace(
            "root_transition = bool(stack) and matched == 0",
            "root_transition = False",
            1,
        ), encoding="utf-8")
        commit(runtime)
        process, result_path, payload = self.run_acceptance(runtime)
        self.assertNotEqual(process.returncode, 0, process.stdout + process.stderr)
        doctor_cases = [case for case in payload["cases"] if case["id"].startswith("doctor-")]
        self.assertTrue(any(case["outcome"] == "accept" and case["exit_code"] == 0
                             for case in doctor_cases))
        self.assertTrue(any(case["targeted_case"] in {"doctor-a1", "doctor-a2"}
                            for case in doctor_cases))
        validator = self.validate(result_path, runtime)
        self.assertEqual(validator.returncode, 1)
        self.assertIn("REJECT", validator.stderr)
        self.assertNotIn("Traceback", validator.stderr)

    def test_migration_mutant_is_rejected_by_canonical_acceptance_contract(self):
        runtime = self.runtime_copy("migration-mutant")
        path = runtime / "scripts/docs-migrate.py"
        text = path.read_text(encoding="utf-8")
        self.assertIn("data = text", text)
        path.write_text(text.replace(
            "data = text",
            'data = getattr(self, "_joined", "") + text.rstrip("\\r\\n")\n'
            "        self._joined = data",
            1,
        ), encoding="utf-8")
        commit(runtime)
        process, result_path, payload = self.run_acceptance(runtime)
        self.assertNotEqual(process.returncode, 0, process.stdout + process.stderr)
        migration_cases = [case for case in payload["cases"]
                           if case["id"].startswith("migration-")]
        self.assertTrue(any(case["outcome"] == "accept" for case in migration_cases))
        self.assertTrue(any(case["targeted_case"] in {
            "migration-split-cdata", "migration-split-pi"
        } for case in migration_cases))
        validator = self.validate(result_path, runtime)
        self.assertEqual(validator.returncode, 1)
        self.assertIn("REJECT", validator.stderr)
        self.assertNotIn("Traceback", validator.stderr)

    def test_mutation_before_refusal_is_rejected_as_state_change(self):
        runtime = self.runtime_copy("mutation-before-refusal")
        path = runtime / "scripts/docs-migrate.py"
        text = path.read_text(encoding="utf-8")
        needle = 'raise ValueError("unmapped record requires context/duplicate disposition and a reason; live findings must be reconciled in STATUS before replanning")'
        self.assertIn(needle, text)
        path.write_text(text.replace(needle,
            '(docs / "STATUS.md").write_text("MUTATED\\n", encoding="utf-8")\n        ' + needle, 1), encoding="utf-8")
        commit(runtime)
        process, result_path, payload = self.run_acceptance(runtime)
        self.assertNotEqual(process.returncode, 0)
        migration = [case for case in payload["cases"] if case["id"].startswith("migration-")]
        self.assertTrue(any(not case["protected_state"]["unchanged"] for case in migration))
        validator = self.validate(result_path, runtime)
        self.assertEqual(validator.returncode, 1)

    def test_strict_validator_rejects_unverified_or_arbitrary_source_and_incomplete_inputs(self):
        runtime = self.runtime_copy("provenance-control")
        commit(runtime)
        process, result_path, payload = self.run_acceptance(runtime)
        self.assertEqual(process.returncode, 0, process.stderr)
        for name, mutate in {
            "unverified": lambda p: p["source_provenance"].update(verified=False),
            "arbitrary-commit": lambda p: p.update(source_commit="0" * 40),
            "missing-input": lambda p: p["runtime_hashes"].pop("tests/acceptance_gate.py"),
        }.items():
            with self.subTest(name=name):
                changed = json.loads(result_path.read_text(encoding="utf-8"))
                mutate(changed)
                changed_path = self.root / f"{name}.json"
                changed_path.write_text(json.dumps(changed), encoding="utf-8")
                validator = self.validate(changed_path, runtime)
                self.assertEqual(validator.returncode, 1, validator.stdout + validator.stderr)

    def test_strict_mode_cannot_be_disabled_by_removing_scope_evidence(self):
        runtime = self.runtime_copy("scope-mutant")
        commit(runtime)
        process, result_path, payload = self.run_acceptance(runtime)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(payload["evidence_scope"], "core-doctor-migration")
        mutant = json.loads(result_path.read_text(encoding="utf-8"))
        mutant.pop("evidence_scope")
        mutant_path = self.root / "scope-mutant-result.json"
        mutant_path.write_text(json.dumps(mutant), encoding="utf-8")
        validator = self.validate(mutant_path, runtime)
        self.assertEqual(validator.returncode, 1)
        self.assertIn("REJECT", validator.stderr)


if __name__ == "__main__":
    unittest.main()
