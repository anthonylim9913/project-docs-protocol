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
        # The fixture is also a harness file, so the validator refuses before scope is computed.
        (self.root/'tests/fixtures/migration-20/STATUS.md').unlink()
        self.reject('harness file missing or unreadable: tests/fixtures/migration-20/STATUS.md')

    def test_missing_required_companion_document(self):
        (self.root/'staging/research-protocol/SKILL.md').unlink()
        self.reject('required input missing')

    def test_missing_required_template(self):
        (self.root/'templates/README.md').unlink()
        self.reject('required input missing')

    def test_input_parent_symlink(self):
        (self.root/'scripts').rename(self.directory/'outside-scripts')
        (self.root/'scripts').symlink_to(self.directory/'outside-scripts', target_is_directory=True)
        self.reject('required input missing or linked')

    def test_harness_parent_symlink(self):
        (self.root/'templates').rename(self.directory/'outside-templates')
        (self.root/'templates').symlink_to(self.directory/'outside-templates', target_is_directory=True)
        self.reject('harness file is linked: templates/LEDGER.md')

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
        self.assertIn('behavior inputs must be clean before manifest generation: scripts/file with spaces.py', rejected.stderr)

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

    def add_document(self, name='docs/NEW-RULES.md'):
        (self.root/name).write_text('# New normative rule\n')
        commit(self.root)
        return name

    def test_new_normative_document_is_bound_by_default(self):
        name = self.add_document()
        out = self.directory/'input.json'
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(name, json.loads(out.read_text())['files'])

    def test_new_normative_document_missing_from_old_hashes_is_rejected(self):
        self.add_document()
        self.reject('runtime hash manifest scope')

    def test_new_normative_document_one_byte_change(self):
        name = self.add_document()
        self.packet, self.hashes = generate(self.root, self.directory)
        self.assertIn(name, json.loads(self.hashes.read_text()))
        self.assertEqual(validate(self.root, self.directory, self.packet, self.hashes).returncode, 0)
        target = self.root/name
        target.write_bytes(target.read_bytes() + b'x')
        self.reject('runtime input hash mismatch')

    def test_new_normative_document_omitted_from_both_hash_sets(self):
        name = self.add_document()
        self.packet, self.hashes = generate(self.root, self.directory)
        self.packet['runtime_hashes'].pop(name)
        self.hashes.write_text(json.dumps(self.packet['runtime_hashes']))
        self.reject('runtime hash manifest scope')

    def test_new_normative_document_deletion(self):
        name = self.add_document()
        (self.root/name).unlink()
        self.reject('required input missing')

    def test_new_untracked_document_is_not_ignored(self):
        (self.root/'docs/UNTRACKED-RULES.md').write_text('# rule\n')
        out = self.directory/'input.json'
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 2)
        self.assertIn('behavior inputs must be clean', p.stderr)

    def test_new_root_file_and_new_directory_are_bound(self):
        (self.root/'extras').mkdir()
        (self.root/'extras/RULES.md').write_text('# rule\n')
        (self.root/'CONTRIBUTING.md').write_text('# rule\n')
        commit(self.root)
        out = self.directory/'input.json'
        self.assertEqual(invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out).returncode, 0)
        files = json.loads(out.read_text())['files']
        self.assertLessEqual({'extras/RULES.md', 'CONTRIBUTING.md'}, set(files))

    def test_exclusions_are_exactly_the_reviewed_list(self):
        from tests import input_manifest
        self.assertEqual(set(input_manifest.EXCLUDED), {
            'docs/STATUS.md', 'docs/CHANGELOG.md', 'docs/DECISIONS.md', 'docs/LEDGER.md',
            'docs/LEDGER-ARCHIVE.md', 'docs/HARDENING-REVIEW.md', 'docs/LESSONS-REVIEW.md'})
        self.assertEqual(input_manifest.EXCLUDED_DIRECTORIES, ('.git/', 'tests/.tmp/'))
        self.assertEqual(input_manifest.SKIPPED_BASENAMES, frozenset({'.DS_Store'}))
        for name in input_manifest.EXCLUDED:
            self.assertTrue((self.root/name).is_file(), 'stale exclusion: ' + name)

    def test_every_tracked_file_is_bound_or_explicitly_excluded(self):
        # Compared with the generator's own output, not the test helper's restatement of the rule.
        from tests import input_manifest
        out = self.directory/'input.json'
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 0, p.stderr)
        tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=self.root, text=True).split('\0')) - {''}
        bound = set(json.loads(out.read_text())['files'])
        self.assertEqual(bound, tracked - set(input_manifest.EXCLUDED))

    # R5: macOS Finder metadata is skipped by name when untracked or ignored; a committed one is
    # bound like any tracked file (D-0028), and nothing else that is ignored is skipped.

    def test_ignored_ds_store_is_skipped_by_name(self):
        self.assertIn('.DS_Store', (self.root/'.gitignore').read_text().split())
        for name in ('.DS_Store', 'docs/.DS_Store', 'tests/.DS_Store'):
            (self.root/name).write_bytes(b'\0\0\0\1Bud1')
        out = self.directory/'input.json'
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse([n for n in json.loads(out.read_text())['files'] if n.endswith('.DS_Store')])
        self.packet, self.hashes = generate(self.root, self.directory)
        result = validate(self.root, self.directory, self.packet, self.hashes)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_untracked_unignored_ds_store_is_skipped_by_name(self):
        gitignore = self.root/'.gitignore'
        gitignore.write_text(''.join(l + '\n' for l in gitignore.read_text().split() if l != '.DS_Store'))
        commit(self.root)
        (self.root/'docs/.DS_Store').write_bytes(b'\0\0\0\1Bud1')
        self.assertIn('?? docs/.DS_Store', subprocess.check_output(['git', 'status', '--porcelain'], cwd=self.root, text=True))
        out = self.directory/'input.json'
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn('docs/.DS_Store', json.loads(out.read_text())['files'])

    def test_committed_ds_store_is_bound_like_any_tracked_file(self):
        before = self.directory/'before.json'
        self.assertEqual(invoke(self.root, 'tests/input_manifest.py', self.root, '--out', before).returncode, 0)
        (self.root/'docs/.DS_Store').write_bytes(b'\0\0\0\1Bud1')
        subprocess.run(['git', 'add', '-f', 'docs/.DS_Store'], cwd=self.root, check=True)
        commit(self.root)
        out = self.directory/'input.json'
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 0, p.stderr)
        manifest = json.loads(out.read_text())
        self.assertIn('docs/.DS_Store', manifest['files'])
        self.assertNotEqual(manifest['tree_sha256'], json.loads(before.read_text())['tree_sha256'])
        self.packet, self.hashes = generate(self.root, self.directory)
        self.assertIn('docs/.DS_Store', self.packet['runtime_hashes'])
        self.assertEqual(validate(self.root, self.directory, self.packet, self.hashes).returncode, 0)
        target = self.root/'docs/.DS_Store'
        target.write_bytes(target.read_bytes() + b'x')
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', out)
        self.assertEqual(p.returncode, 2)
        self.assertIn('must be clean before manifest generation: docs/.DS_Store', p.stderr)
        self.reject('runtime input hash mismatch')
        target.unlink()
        self.reject('required input missing')

    def test_manifest_cli_reruns_itself_isolated(self):
        marker = self.directory/'planted-ran'
        (self.root/'tests/json.py').write_text(
            'import pathlib\npathlib.Path(%r).write_text("ran")\nraise SystemExit(0)\n' % str(marker))
        from tests import input_manifest
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--print-harness-digest')
        self.assertFalse(marker.exists(), 'input_manifest.py imported a module planted in tests/')
        self.assertEqual((p.returncode, p.stdout.strip()), (0, input_manifest.harness_digest(self.root)), p.stderr)

    def test_ds_store_rule_does_not_skip_other_ignored_files(self):
        (self.root/'.DS_Store').write_bytes(b'\0')
        (self.root/'scripts/.DS_Store.py').write_text('# importable\n')
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.directory/'input.json')
        self.assertEqual(p.returncode, 2)
        self.assertIn('must be clean before manifest generation: scripts/.DS_Store.py', p.stderr)
        self.assertNotIn(': .DS_Store', p.stderr)

    # R2: bytecode and import hooks are refused, never left out of scope.

    def test_bytecode_and_import_hooks_are_refused_committed_or_not(self):
        import py_compile, sys
        names = ['scripts/__pycache__/register_paths.%s.pyc' % sys.implementation.cache_tag,
                 'scripts/helper.pyc', 'scripts/helper.pyo', 'scripts/_speedups.so', 'scripts/_speedups.pyd',
                 'scripts/hook.pth']
        for name in names:
            for committed in (False, True):
                with self.subTest(name=name, committed=committed):
                    path = self.root/name
                    path.parent.mkdir(exist_ok=True)
                    if name.endswith('.pyc'):
                        py_compile.compile(str(self.root/'scripts/register_paths.py'), cfile=str(path))
                    else:
                        path.write_text('import os\n')
                    if committed:
                        subprocess.run(['git', 'add', '-f', name], cwd=self.root, check=True)
                        commit(self.root)
                    p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.directory/'input.json')
                    self.assertEqual(p.returncode, 2, p.stdout)
                    self.assertIn('bytecode or import hook in the reviewed tree (remove it): ' + name, p.stderr)
                    self.reject('bytecode or import hook in the reviewed tree (remove it): ' + name)
                    path.unlink()
                    if committed:
                        subprocess.run(['git', 'rm', '-q', '--cached', '--ignore-unmatch', name], cwd=self.root, check=True)
                        commit(self.root)

    def test_committed_bytecode_changes_behavior_the_manifest_would_not_see(self):
        # Why R2 refuses rather than skips: Python runs the pyc although the .py is unchanged.
        import py_compile, sys
        evil = self.directory/'register_paths.py'
        evil.write_text((self.root/'scripts/register_paths.py').read_text() + '\nraise SystemExit("replaced by bytecode")\n')
        name = 'scripts/__pycache__/register_paths.%s.pyc' % sys.implementation.cache_tag
        (self.root/name).parent.mkdir()
        py_compile.compile(str(evil), cfile=str(self.root/name), invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
        subprocess.run(['git', 'add', '-f', name], cwd=self.root, check=True)
        commit(self.root)
        doctor = invoke(self.root, 'scripts/docs-doctor.py', '.', '--no-git')
        # With a pycache prefix (PYTHONPYCACHEPREFIX, -X pycache_prefix) Python never reads a
        # __pycache__ beside the source, so the premise holds only without one; the refusal holds either way.
        if sys.pycache_prefix is None:
            self.assertIn('replaced by bytecode', doctor.stderr)
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.directory/'input.json')
        self.assertEqual(p.returncode, 2)
        self.assertIn(name, p.stderr)


if __name__ == '__main__':
    unittest.main()

# New frozen D authority is part of the core manifest's declared dependencies.
