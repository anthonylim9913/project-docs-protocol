"""Named CLI regressions must fail when their corresponding guard is removed.

Mutations occur only in disposable committed copies. The exact named regression
first passes intact, then fails because the intended contract is violated,
not because the fixture broke, Git was dirty, or another diagnostic was emitted.
The summary-selector mutant restores a known false rejection of valid prose.
"""
from pathlib import Path
import tempfile
import unittest
from tests.acceptance_support import copy_subject, commit, invoke


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

    def test_journal_schema_guard(self):
        self.removal('test_journal_schema_downgrade', "journal['version'] == 1", 'True')

    def test_ledger_row_semantics_guard(self):
        self.removal('test_ledger_row_state', 'rows == expected_rows', 'True')

    def test_doctor_exhaustive_line_guard(self):
        self.removal('test_malformed_extra_doctor_warning', "require(complete_lines, 'doctor line schema: unmatched or misplaced nonblank line')", 'pass')

    def test_journal_target_schema_guard(self):
        self.removal('test_journal_extra_target_key', "set(target) == {'content', 'after'}", 'True')


if __name__ == '__main__':
    unittest.main()
