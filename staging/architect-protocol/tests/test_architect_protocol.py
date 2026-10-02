"""Public example, optional absence, and the repaired named R4 regression."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import packet_fixture as f
import test_architect_binding as binding


class ArchitectProtocolTests(unittest.TestCase):
    setUp=binding.ArchitectBindingTests.setUp
    cli=binding.ArchitectBindingTests.cli
    accepted=binding.ArchitectBindingTests.accepted
    rejected=binding.ArchitectBindingTests.rejected
    alter_review=binding.ArchitectBindingTests.alter_review

    def test_doctor_rejects_subject_mismatched_reviewer_result(self):
        """Valid committed control is proved in setUp; only reviewer subject changes."""
        self.alter_review('subject_commit',self.packet['reporting'])
        self.rejected('reviewer subject mismatch')

    def test_absent_packet_skips(self):
        shutil.rmtree(self.root/'docs/architect')
        result=self.cli();self.assertEqual(result.returncode,0,result.stdout)
        self.assertIn('SKIP architect: packet absent',result.stdout)

    def test_example_is_explicit_and_has_no_acceptance(self):
        shutil.rmtree(self.root/'docs/architect')
        shutil.copytree(binding.ROOT/'examples/minimal/docs/architect',self.root/'docs/architect')
        self.rejected('explicit --structural-example')
        result=self.cli('--structural-example')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('STRUCTURAL architect',result.stdout);self.assertNotIn('PASS',result.stdout)

    def test_missing_stage_artifact_rejects_itself(self):
        (self.root/'docs/architect/STAGES.md').unlink()
        self.rejected('STAGES.md missing')

    def test_competing_status_rejects_itself(self):
        (self.root/'docs/architect/STATUS.md').write_text('# competing dashboard\n')
        self.rejected('competing STATUS.md')

    def test_skill_has_standard_frontmatter_and_boundaries(self):
        text=(binding.ROOT/'SKILL.md').read_text()
        self.assertTrue(text.startswith('---\n'));header,body=text.split('\n---\n',1)
        self.assertIn('name: architect-protocol',header)
        for phrase in ('independent reviewer','docs/STATUS.md','schema 2','SCHEMA.md'):
            self.assertIn(phrase,body)


if __name__=='__main__':unittest.main()
