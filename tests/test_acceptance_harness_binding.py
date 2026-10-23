"""LG-0044(b): the validator and the modules it relies on are verified before they judge.

Each case starts from a passing complete packet in a disposable committed copy,
changes the harness (never the packet's evidence of the product), and shows the
change is refused instead of being approved by the changed code itself.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tests import input_manifest
from tests.acceptance_support import ROOT, copy_subject, generate, invoke, MANIFEST

VALIDATOR = 'tests/validate_acceptance.py'


class HarnessBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='harness binding ')
        cls.directory = Path(cls.temp.name)
        cls.root = cls.directory / 'subject'
        copy_subject(cls.root)
        cls.packet, cls.hashes = generate(cls.root, cls.directory)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_validator(self, packet=None, *extra):
        path = self.directory / 'packet.json'
        path.write_text(json.dumps(self.packet if packet is None else packet))
        return invoke(self.root, VALIDATOR, path, MANIFEST, self.hashes, *extra)

    def edited(self, name, transform):
        target = self.root / name
        original = target.read_bytes()
        self.addCleanup(target.write_bytes, original)
        target.write_bytes(transform(original))

    def test_control_unchanged_harness_is_accepted(self):
        p = self.run_validator()
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_validator_edited_to_skip_canonical_checks_cannot_approve_itself(self):
        forged = json.loads(json.dumps(self.packet))
        forged.pop('evidence_scope')
        control = self.run_validator(forged)
        self.assertEqual(control.returncode, 1)
        self.assertIn('canonical evidence scope', control.stderr)
        self.edited(VALIDATOR, lambda b: b.replace(b'strict=True)', b'strict=False)', 1))
        self.assertNotEqual(self.root.joinpath(VALIDATOR).read_bytes(), b'')
        p = self.run_validator(forged)
        self.assertEqual(p.returncode, 1, 'edited validator approved its own run: ' + p.stdout)
        self.assertIn('harness', p.stderr)

    def test_one_byte_change_to_each_harness_file_is_rejected(self):
        self.assertGreaterEqual(len(input_manifest.HARNESS_FILES), 6)
        for name in input_manifest.HARNESS_FILES:
            with self.subTest(name=name):
                saved = (self.root / name).read_bytes()
                self.edited(name, lambda b: b + b' ')
                p = self.run_validator()
                self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
                self.assertIn('harness digest does not match', p.stderr)
                self.assertNotIn('Traceback', p.stderr)
                (self.root / name).write_bytes(saved)

    def test_harness_module_deleted_is_not_approved(self):
        target = self.root / 'tests/acceptance_gate.py'
        original = target.read_bytes()
        self.addCleanup(target.write_bytes, original)
        target.unlink()
        p = self.run_validator()
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertNotIn('"accepted"', p.stdout)

    def test_harness_file_deleted_is_rejected(self):
        name = 'tests/fixtures/hardening-2026-09-12/acceptance-cases.json'
        target = self.root / name
        original = target.read_bytes()
        self.addCleanup(target.write_bytes, original)
        target.unlink()
        p = self.run_validator()
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn('harness', p.stderr)

    def test_record_missing_or_altered_is_rejected(self):
        record = self.root / input_manifest.HARNESS_RECORD
        original = record.read_bytes()
        self.addCleanup(record.write_bytes, original)
        record.write_text('0' * 64 + '\n')
        p = self.run_validator()
        self.assertEqual((p.returncode, 'harness digest does not match' in p.stderr), (1, True), p.stderr)
        record.unlink()
        p = self.run_validator()
        self.assertEqual(p.returncode, 1)
        self.assertIn('harness digest record', p.stderr)

    def test_reviewer_pin_must_match_the_running_harness(self):
        digest = input_manifest.harness_digest(self.root)
        ok = self.run_validator(None, '--harness-sha256', digest)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        for bad in ('0' * 64, 'not-a-digest', digest.upper()):
            with self.subTest(pin=bad):
                p = self.run_validator(None, '--harness-sha256', bad)
                self.assertEqual(p.returncode, 1, p.stdout)
                self.assertIn('harness', p.stderr)

    def test_pin_without_value_is_a_usage_error(self):
        p = self.run_validator(None, '--harness-sha256')
        self.assertEqual(p.returncode, 2)

    def test_record_is_current_and_not_part_of_its_own_digest(self):
        self.assertNotIn(input_manifest.HARNESS_RECORD, input_manifest.HARNESS_FILES)
        recorded = (ROOT / input_manifest.HARNESS_RECORD).read_text().strip()
        self.assertEqual(recorded, input_manifest.harness_digest(ROOT))

    def test_digest_command_prints_what_a_reviewer_pins(self):
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--print-harness-digest')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), input_manifest.harness_digest(self.root))

    def test_harness_files_are_inside_the_bound_input_scope(self):
        bound = set(json.loads(self.hashes.read_text()))
        self.assertLessEqual(set(input_manifest.HARNESS_FILES) | {input_manifest.HARNESS_RECORD}, bound)


if __name__ == '__main__':
    unittest.main()
