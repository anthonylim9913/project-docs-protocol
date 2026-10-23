"""Named CLI regressions must fail when their corresponding guard is removed.

Mutations occur only in disposable committed copies. The exact named regression
first passes intact, then fails because the intended contract is violated,
not because the fixture broke, Git was dirty, or another diagnostic was emitted.
The summary-selector mutant restores a known false rejection of valid prose.
"""
import json
from pathlib import Path
import tempfile
import unittest
from tests import input_manifest
from tests.acceptance_support import MANIFEST, copy_subject, commit, external, generate, invoke


class AcceptanceGuardRemovalTests(unittest.TestCase):
    def removal(self, test, needle, replacement, module="tests.test_acceptance_cli.AcceptanceCliTests", source="tests/acceptance_evidence.py", assertion="AssertionError: 0 != 1"):
        with tempfile.TemporaryDirectory(prefix='guard removal ') as directory:
            root = Path(directory)/'subject'
            copy_subject(root)
            command = ['-m', 'unittest', module + '.' + test, '-v']
            control = invoke(root, *command)
            self.assertEqual(control.returncode, 0, control.stdout + control.stderr)
            path = root/source
            text = path.read_text()
            self.assertEqual(text.count(needle), 1, 'mutation must match one specific guard')
            path.write_text(text.replace(needle, replacement, 1))
            # An honest coordinated edit re-records the harness digest; these cases isolate the named guard.
            (root/input_manifest.HARNESS_RECORD).write_text(input_manifest.harness_record(root))
            commit(root)
            mutant = invoke(root, *command)
            self.assertEqual(mutant.returncode, 1, mutant.stdout + mutant.stderr)
            self.assertIn(assertion, mutant.stderr)
            self.assertIn('FAILED (failures=1)', mutant.stderr)
            self.assertNotIn('ERROR:', mutant.stderr)

    def test_raw_snapshot_addition_guard(self):
        self.removal('test_canonical_rejects_unauthorized_file_evidence',
                     "set(after) == set(before) | set(additions)", 'True')

    def test_tree_digest_guard(self):
        self.removal('test_false_tree_digest',
                     "provenance.get('runtime_tree_sha256') == tree_hash(values)", 'True')

    def test_positive_identity_guard(self):
        self.removal('test_wrong_positive_identity',
                     "positive.get('name') == rule['positive']", 'True')

    def test_stage_identity_guard(self):
        self.removal('test_wrong_stage_name', "item.get('name') == name", 'True')

    def test_raw_snapshot_equality_guard(self):
        self.removal('test_contradictory_protected_state',
                     "all(after[k] == v for k, v in before.items() if k not in mutable)", 'True')

    def test_actual_diagnostic_guard(self):
        self.removal('test_wrong_doctor_summary_counts', 'summaries == [summary]', 'True')

    def test_summary_selector_preserves_descriptive_prose(self):
        self.removal('test_doctor_description_with_summary_words_remains_valid',
                     "re.match(r'^[0-9]+ checks:', line)", "' checks:' in line",
                     assertion='AssertionError: 1 != 0 : REJECT: doctor summary does not match observations')

    def test_commit_blob_binding_guard(self):
        self.removal('test_assume_unchanged_cannot_hide_modified_behavior',
                     "dirty.update(p for p in current if current[p] != committed[p])", 'pass',
                     module='tests.test_input_manifest_cli.InputManifestCliTests', source='tests/input_manifest.py',
                     assertion='AssertionError: 0 != 2')

    def test_harness_binding_guard(self):
        self.removal('test_validator_edited_to_skip_canonical_checks_cannot_approve_itself',
                     "    blobs = verified_bytes(root, entries)", "    blobs = {n: (root / n).read_bytes() for n in entries}",
                     module='tests.test_acceptance_harness_binding.HarnessBindingTests',
                     source='tests/validate_acceptance.py', assertion='AssertionError: 0 != 1 : edited validator approved its own run')

    def test_shadow_scan_guard(self):
        # Without the scan the planted package is still never imported: the harness loads from
        # verified bytes, so the real gate runs and refuses the forged packet on its own grounds.
        self.removal('test_shadowing_package_is_refused', '    planted = shadowing(root)\n', '    planted = []\n',
                     module='tests.test_acceptance_harness_binding.HarnessBindingTests',
                     source='tests/validate_acceptance.py',
                     assertion="not found in 'REJECT: canonical evidence scope is missing or untrusted")

    def test_journal_schema_guard(self):
        self.removal('test_journal_schema_downgrade', "journal['version'] == 1", 'True')

    def test_ledger_row_semantics_guard(self):
        self.removal('test_ledger_row_state', 'rows == expected_rows', 'True')

    def test_doctor_exhaustive_line_guard(self):
        self.removal('test_malformed_extra_doctor_warning', "require(complete_lines, 'doctor line schema: unmatched or misplaced nonblank line')", 'pass')

    def test_journal_target_schema_guard(self):
        self.removal('test_journal_extra_target_key', "set(target) == {'content', 'after'}", 'True')



class InTreeLimitTests(unittest.TestCase):
    """The documented limit of the in-tree check, tested rather than asserted (D-0025).

    Each mutant edits the judging code inside the candidate and does not re-record. The
    candidate's own validator then approves a packet the real gate rejects, because code in a
    tree cannot vouch for itself. The external check, a trusted checkout's runner and validator
    judging the candidate, refuses every one.
    """
    MUTANTS = {
        # The refusal after a failed harness check no longer fails the run (the review's line-60 mutant).
        'refusal-exit': [('tests/validate_acceptance.py',
                          '        print(f"REJECT: {error}", file=sys.stderr)\n        return 1\n    GateError',
                          '        print(f"REJECT: {error}", file=sys.stderr)\n        return 0\n    GateError')],
        # The digest comparison never fails, and strictness is off (the review's line-160 mutant).
        'digest-comparison': [('tests/validate_acceptance.py', '    if changed:\n', '    if False:\n'),
                              ('tests/validate_acceptance.py', 'strict=True,', 'strict=False,')],
        # The verification call is gone and strictness is off; passes even with the correct pin.
        'verification-removed': [('tests/validate_acceptance.py', '    entries = read_record(root, pinned)\n',
                                  '    entries = read_record(root)\n'),
                                 ('tests/validate_acceptance.py', '    blobs = verified_bytes(root, entries)\n',
                                  '    blobs = {n: (root / n).read_bytes() for n in entries}\n'),
                                 ('tests/validate_acceptance.py', 'strict=True,', 'strict=False,')],
    }

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='in-tree limit ')
        cls.trusted = Path(cls.temp.name) / 'trusted'
        copy_subject(cls.trusted)
        cls.pin = __import__('hashlib').sha256((cls.trusted / input_manifest.HARNESS_RECORD).read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_in_tree_check_is_defeated_and_external_check_refuses(self):
        for name, edits in self.MUTANTS.items():
            with self.subTest(mutant=name), tempfile.TemporaryDirectory(prefix='in-tree limit ') as directory:
                directory = Path(directory)
                root = directory / 'candidate'
                copy_subject(root)
                packet, hashes = generate(root, directory)
                for source, needle, replacement in edits:
                    text = (root / source).read_text()
                    self.assertEqual(text.count(needle), 1, needle)
                    (root / source).write_text(text.replace(needle, replacement, 1))
                commit(root)
                packet.pop('evidence_scope')
                path = directory / 'forged.json'
                path.write_text(json.dumps(packet))
                pin = ('--harness-sha256', self.pin) if name == 'verification-removed' else ()
                inside = invoke(root, 'tests/validate_acceptance.py', *pin, path, MANIFEST, hashes)
                self.assertEqual(inside.returncode, 0, 'in-tree limit no longer holds; update D-0025: ' + inside.stderr)
                _, outside = external(self.trusted, root, directory, '--harness-sha256', self.pin)
                self.assertEqual(outside.returncode, 1, outside.stdout)
                self.assertIn('REJECT: candidate judging files differ from the trusted checkout: tests/validate_acceptance.py',
                              outside.stderr)


if __name__ == '__main__':
    unittest.main()
