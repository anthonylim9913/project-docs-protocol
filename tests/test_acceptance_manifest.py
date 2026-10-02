"""Validate the frozen, hand-authored hardening acceptance inventory."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "tests/fixtures/hardening-2026-09-12"


class AcceptanceManifestTests(unittest.TestCase):
    def test_manifest_has_exact_fixture_bytes_and_hand_authored_expectations(self):
        manifest = json.loads((BUNDLE / "acceptance-cases.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], 1)
        self.assertIn("hand-authored", manifest["oracle"])
        ids = [case["id"] for case in manifest["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        for case in manifest["cases"]:
            fixture = BUNDLE / case["fixture"]
            self.assertTrue(fixture.is_file(), case["id"])
            raw = fixture.read_bytes()
            self.assertTrue(raw, case["id"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), case["fixture_sha256"])
            for key in ("classification", "inventory", "write", "exit", "positive", "scope", "assertion"):
                self.assertIn(key, case)
        self.assertEqual({"doctor-a1", "doctor-a2", "migration-split-cdata", "migration-split-pi"}, set(ids))


if __name__ == "__main__":
    unittest.main()
