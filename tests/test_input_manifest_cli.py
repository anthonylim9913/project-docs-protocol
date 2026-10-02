"""Independent scope/CLI controls; fixture paths never come from child output."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from tests.acceptance_support import copy_subject, generate, validate, invoke, commit, MANIFEST


class InputManifestCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='input scope ')
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.root = self.directory / 'subject'
        copy_subject(self.root)
        self.packet, self.hashes = generate(self.root, self.directory)
        self.assertEqual(validate(self.root, self.directory, self.packet, self.hashes).returncode, 0)

    def reject(self, diagnostic):
        result = validate(self.root, self.directory, self.packet, self.hashes)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_complete_inputs_include_shipped_guidance_templates_and_fixture(self):
        out = self.directory / 'input.json'
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 0, p.stderr)
        actual = json.loads(out.read_text())
        expected = json.loads(self.hashes.read_text())
        self.assertEqual(actual['files'], expected)
        required = {'SKILL.md', 'AGENTS.md', 'CLAUDE.md', 'templates/README.md', 'templates/STATUS.md',
                    'templates/CHANGELOG.md', 'templates/DECISIONS.md', 'tests/fixtures/migration-20/STATUS.md',
                    'docs/BRIEF-EXAMPLE.md', 'docs/EVIDENCE.md', 'docs/PROTOCOLS.md',
                    'staging/architect-protocol/SKILL.md', 'staging/research-protocol/SKILL.md',
                    'staging/architect-protocol/SCHEMA.md', 'staging/architect-protocol/scripts/architect_packet.py',
                    'staging/architect-protocol/tests/test_architect_lifecycle.py',
                    'staging/architect-protocol/tests/test_architect_binding.py'}
        self.assertLessEqual(required, set(actual['files']))
        representation = ''.join(p + ':' + expected[p] + '\n' for p in sorted(expected))
        self.assertEqual(actual['tree_sha256'], hashlib.sha256(representation.encode()).hexdigest())

    def test_omission_in_both_packet_and_external_hashes(self):
        self.packet['runtime_hashes'].pop('SKILL.md')
        self.hashes.write_text(json.dumps(self.packet['runtime_hashes']))
        self.reject('runtime hash manifest scope')

    def test_extra_scope_in_both_packet_and_external_hashes(self):
        self.packet['runtime_hashes']['docs/STATUS.md'] = hashlib.sha256((self.root/'docs/STATUS.md').read_bytes()).hexdigest()
        self.hashes.write_text(json.dumps(self.packet['runtime_hashes']))
        self.reject('runtime hash manifest scope')

    def test_stale_hash_in_both_packet_and_external_hashes(self):
        self.packet['runtime_hashes']['SKILL.md'] = '0'*64
        self.hashes.write_text(json.dumps(self.packet['runtime_hashes']))
        self.reject('runtime input hash mismatch')

    def test_wrong_hash_input_type(self):
        self.hashes.write_text('[]')
        self.reject('runtime hash input')

    def test_missing_required_fixture(self):
        (self.root/'tests/fixtures/migration-20/STATUS.md').unlink()
        self.reject('required input missing')

    def test_missing_required_template(self):
        (self.root/'templates/README.md').unlink()
        self.reject('required input missing')

    def test_input_parent_symlink(self):
        (self.root/'templates').rename(self.directory/'outside-templates')
        (self.root/'templates').symlink_to(self.directory/'outside-templates', target_is_directory=True)
        self.reject('required input missing or linked')

    def test_untracked_behavior_path_with_spaces(self):
        (self.root/'scripts/file with spaces.py').write_text('# new input\n')
        self.reject('runtime hash manifest scope')

    def test_manifest_cli_refuses_dirty_spaced_input(self):
        out = self.directory/'input.json'
        (self.root/'scripts/file with spaces.py').write_text('# first\n')
        commit(self.root)
        positive = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(positive.returncode, 0, positive.stderr)
        (self.root/'scripts/file with spaces.py').write_text('# modified\n')
        rejected = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(rejected.returncode, 2)
        self.assertIn('behavior inputs must be clean', rejected.stderr)

    def test_input_manifest_output_cannot_create_self_reference(self):
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.root/'tests/generated.json')
        self.assertEqual(p.returncode, 2)
        self.assertIn('outside the reviewed tree', p.stderr)
        self.assertFalse((self.root/'tests/generated.json').exists())

    def test_duplicate_json_key(self):
        path = self.directory/'duplicate.json'
        path.write_text(json.dumps(self.packet)[:-1] + ', "schema": 2}')
        p = invoke(self.root, 'tests/validate_acceptance.py', path, MANIFEST, self.hashes)
        self.assertEqual(p.returncode, 1)
        self.assertIn('duplicate JSON key: schema', p.stderr)

    def test_invalid_json_is_the_actual_refusal(self):
        path = self.directory/'malformed.json'
        path.write_text('{ not valid JSON')
        p = invoke(self.root, 'tests/validate_acceptance.py', path, MANIFEST, self.hashes)
        self.assertEqual(p.returncode, 1)
        self.assertIn('Expecting property name', p.stderr)

    def test_ignored_untracked_input_cannot_bind_to_committed_subject(self):
        (self.root/'.gitignore').write_text('scripts/ignored-helper.py\n')
        commit(self.root)
        out = self.directory/'input.json'
        positive = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(positive.returncode, 0, positive.stderr)
        (self.root/'scripts/ignored-helper.py').write_text('# ignored behavior\n')
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 2)
        self.assertIn('behavior inputs must be clean', p.stderr)

    def test_nonportable_behavior_path_is_rejected_not_omitted(self):
        (self.root/'scripts/helper:bad.py').write_text('# invalid path\n')
        self.reject('unsupported behavior input path')

    def test_normative_dependencies_are_in_manifest(self):
        names = json.loads(self.hashes.read_text())
        for name in ('docs/README.md', 'docs/MIGRATION.md', 'docs/PROTOCOLS.md',
                     'docs/SKILL-REGISTRY.md', 'docs/BRIEF-EXAMPLE.md', 'docs/EVIDENCE.md'):
            self.assertIn(name, names)

    def test_normative_document_cannot_be_omitted(self):
        name='docs/PROTOCOLS.md'
        self.packet['runtime_hashes'].pop(name)
        self.hashes.write_text(json.dumps(self.packet['runtime_hashes']))
        self.reject('runtime hash manifest scope')

    def test_normative_document_dirty_change(self):
        name='docs/SKILL-REGISTRY.md'
        target=self.root/name;target.write_text(target.read_text()+'\nDifferent authority.\n')
        self.reject('runtime input hash mismatch')

    def test_assume_unchanged_cannot_hide_modified_behavior(self):
        self.flagged_change('--assume-unchanged')

    def test_skip_worktree_cannot_hide_modified_behavior(self):
        self.flagged_change('--skip-worktree')

    def flagged_change(self, flag):
        subprocess.run(['git', 'update-index', flag, 'SKILL.md'], cwd=self.root, check=True)
        target = self.root/'SKILL.md'
        target.write_text(target.read_text() + '\nModified behavior behind index flag.\n')
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.directory/'flagged.json')
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn('behavior inputs must be clean', p.stderr)

    def test_manifest_output_hardlink_cannot_modify_input(self):
        target = self.root/'SKILL.md'
        before = hashlib.sha256(target.read_bytes()).hexdigest()
        out = self.directory/'alias.json'
        os.link(target, out)
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn('output must be a regular unlinked file', p.stderr)
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), before)

    def test_normative_input_deletion(self):
        (self.root/'docs/PROTOCOLS.md').unlink()
        self.reject('required input missing')

    def test_normative_input_omission(self):
        self.packet['runtime_hashes'].pop('docs/MIGRATION.md')
        self.hashes.write_text(json.dumps(self.packet['runtime_hashes']))
        self.reject('runtime hash manifest scope')

    def test_normative_input_dirty_change(self):
        name='docs/EVIDENCE.md'
        target=self.root/name
        target.write_text(target.read_text() + '\nDifferent authority.\n')
        self.reject('runtime input hash mismatch')

    def test_flagged_working_bytes_rejected_by_validator(self):
        subprocess.run(['git','update-index','--assume-unchanged','SKILL.md'],cwd=self.root,check=True)
        target=self.root/'SKILL.md'
        target.write_text(target.read_text() + '\nModified hidden behavior.\n')
        digest=hashlib.sha256(target.read_bytes()).hexdigest()
        self.packet['runtime_hashes']['SKILL.md']=digest
        for case in self.packet['cases']:
            case['runtime_hashes']['SKILL.md']=digest
        material=''.join(name+':'+self.packet['runtime_hashes'][name]+'\n' for name in sorted(self.packet['runtime_hashes']))
        self.packet['source_provenance']['runtime_tree_sha256']=hashlib.sha256(material.encode()).hexdigest()
        self.hashes.write_text(json.dumps(self.packet['runtime_hashes']))
        self.reject('source commit does not match a clean reviewed runtime')

    def test_flagged_working_bytes_rejected_by_runner(self):
        subprocess.run(['git','update-index','--skip-worktree','SKILL.md'],cwd=self.root,check=True)
        target=self.root/'SKILL.md'
        target.write_text(target.read_text() + '\nModified hidden behavior.\n')
        path=self.directory/'flagged-result.json'
        p=invoke(self.root,'tests/run_acceptance.py','--runtime-root',self.root,'--source-commit',self.packet['source_commit'],'--result',path)
        self.assertEqual(p.returncode,1,p.stderr)
        self.assertIn('source commit does not match a clean reviewed runtime',json.loads(path.read_text())['failures'][0]['message'])

    def test_manifest_output_symlink_preserves_sentinel(self):
        sentinel=self.directory/'sentinel'; sentinel.write_text('generated safe bytes')
        out=self.directory/'linked.json'; out.symlink_to(sentinel)
        p=invoke(self.root,'tests/input_manifest.py',self.root,'--out',out)
        self.assertEqual(p.returncode,2)
        self.assertIn('output must be a regular unlinked file',p.stderr)
        self.assertEqual(sentinel.read_text(),'generated safe bytes')

    def test_manifest_output_fifo_is_refused_without_hanging(self):
        out=self.directory/'output.fifo'; os.mkfifo(out)
        p=invoke(self.root,'tests/input_manifest.py',self.root,'--out',out)
        self.assertEqual(p.returncode,2)
        self.assertIn('output must be a regular unlinked file',p.stderr)


if __name__ == '__main__':
    unittest.main()

# New frozen D authority is part of the core manifest's declared dependencies.
