"""Privacy scanner tests use only invented secrets and disposable Git history."""
import os
import importlib.util
import io
from contextlib import redirect_stderr
from unittest import mock
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/leak-scan.py'


class LeakScanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1',
                        GIT_CONFIG_GLOBAL=os.devnull, LEAK_SCAN_PATTERNS='')
        for key in list(self.env):
            if key.startswith(('GIT_AUTHOR_', 'GIT_COMMITTER_')):
                del self.env[key]
        self.git('init', '-q')
        self.git('config', 'user.name', 'Example Contributor')
        self.git('config', 'user.email', 'example@example.invalid')
        self.patterns = Path(self.temp.name) / 'patterns.txt'
        self.patterns.write_text('# invented fixture\n\nFABLE_SECRET\n', encoding='utf-8')
        self.base = self.commit('initial', {'safe.txt': 'ordinary\n'})

    def git(self, *args, **kwargs):
        return subprocess.run(['git', *args], cwd=self.root, env=self.env,
                              check=True, capture_output=True, **kwargs).stdout.decode().strip()

    def commit(self, message, files=None):
        for path, data in (files or {}).items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data if isinstance(data, bytes) else data.encode())
        self.git('add', '.')
        self.git('commit', '-q', '--allow-empty', '-m', message)
        return self.git('rev-parse', 'HEAD')

    def scan(self, *args, stdin=None, patterns=True):
        self.assertTrue(SCRIPT.exists(), 'leak-scan.py has not been implemented')
        options = ['--patterns', str(self.patterns)] if patterns else []
        return subprocess.run([sys.executable, '-B', str(SCRIPT), *options, *args],
                              cwd=self.root, env=self.env, input=stdin or '',
                              text=True, capture_output=True)

    def test_no_configuration_is_harmless(self):
        result = self.scan(patterns=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertIn('not configured', result.stdout)

    def test_clean_range(self):
        tip = self.commit('ordinary', {'safe.txt': 'still ordinary\n'})
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('CLEAN', result.stdout)

    def test_changed_blob_reports_only_locations(self):
        tip = self.commit('ordinary', {'safe.txt': 'safe\nFABLE_SECRET hidden\n'})
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(tip, result.stdout)
        self.assertIn('safe.txt', result.stdout)
        self.assertIn('line 2', result.stdout)
        self.assertIn('pattern line 3', result.stdout)
        self.assertNotIn('FABLE_SECRET', result.stdout + result.stderr)
        self.assertNotIn('hidden', result.stdout + result.stderr)

    def test_intermediate_blob_is_scanned_even_if_tip_is_clean(self):
        middle = self.commit('ordinary', {'safe.txt': 'FABLE_SECRET\n'})
        tip = self.commit('ordinary', {'safe.txt': 'clean again\n'})
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(middle, result.stdout)

    def test_complete_changed_blob_includes_unchanged_lines(self):
        before = self.commit('ordinary', {'safe.txt': 'FABLE_SECRET\nold\n'})
        tip = self.commit('ordinary', {'safe.txt': 'FABLE_SECRET\nnew\n'})
        result = self.scan('--range', before + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('line 1', result.stdout)

    def test_deleted_blobs_are_not_scanned(self):
        before = self.commit('ordinary', {'gone.txt': 'FABLE_SECRET\n'})
        self.git('rm', 'gone.txt')
        tip = self.commit('ordinary')
        result = self.scan('--range', before + '..' + tip)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_messages_and_all_four_identity_fields_are_scanned(self):
        fields = {'GIT_AUTHOR_NAME': 'author name', 'GIT_AUTHOR_EMAIL': 'author email',
                  'GIT_COMMITTER_NAME': 'committer name', 'GIT_COMMITTER_EMAIL': 'committer email'}
        for variable, label in fields.items():
            with self.subTest(field=label):
                self.env[variable] = 'FABLE_SECRET@example.invalid'
                tip = self.commit('ordinary')
                del self.env[variable]
                result = self.scan('--range', self.base + '..' + tip)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(label, result.stdout)
                self.assertNotIn('FABLE_SECRET', result.stdout + result.stderr)
                self.base = tip
        tip = self.commit('ordinary\n\nFABLE_SECRET')
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('commit message', result.stdout)
        self.assertIn('line 3', result.stdout)

    def test_binary_skip_and_lenient_text_decoding(self):
        tip = self.commit('ordinary', {'binary.bin': b'\0FABLE_SECRET',
                                       'text.txt': b'\xffFABLE_SECRET\n'})
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('binary skipped 1', result.stdout)
        self.assertIn('text.txt', result.stdout)
        self.assertNotIn('binary.bin', result.stdout)

    def test_invalid_regex_and_missing_configured_file_fail_closed(self):
        for text in ('[', None):
            with self.subTest(text=text):
                if text is None:
                    self.patterns.unlink()
                else:
                    self.patterns.write_text(text, encoding='utf-8')
                result = self.scan('--range', self.base + '..HEAD')
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn(str(self.patterns), result.stdout + result.stderr)

    def test_patterns_symlink_loop_fails_without_private_path(self):
        self.patterns.unlink()
        self.patterns.symlink_to(self.patterns.name)
        result = self.scan('--range', self.base + '..HEAD')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn(str(self.patterns), result.stdout + result.stderr)

    def test_patterns_must_stay_outside_repo_even_through_symlink(self):
        internal = self.root / 'private-patterns'
        internal.write_text('FABLE_SECRET', encoding='utf-8')
        self.patterns.unlink()
        self.patterns.symlink_to(internal)
        result = self.scan('--range', self.base + '..HEAD')
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_external_git_metadata_is_still_inside_repository(self):
        self.root = Path(self.temp.name) / 'separate-repo'
        self.root.mkdir()
        metadata = Path(self.temp.name) / 'metadata'
        self.git('init', '-q', '--separate-git-dir', str(metadata))
        self.git('config', 'user.name', 'Example Contributor')
        self.git('config', 'user.email', 'example@example.invalid')
        self.base = self.commit('initial')
        self.patterns = metadata / 'patterns.txt'
        self.patterns.write_text('FABLE_SECRET', encoding='utf-8')
        result = self.scan('--range', self.base + '..HEAD')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_repository_with_trailing_space_cannot_hide_internal_patterns(self):
        moved = self.root.with_name('repo ')
        self.root.rename(moved)
        self.root = moved
        self.patterns = self.root / 'patterns.txt'
        self.patterns.write_text('FABLE_SECRET', encoding='utf-8')
        result = self.scan('--range', self.base + '..HEAD')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_sample_hook_forwards_stdin_without_remote_arguments(self):
        scripts = self.root / 'scripts'
        scripts.mkdir()
        self.assertTrue(SCRIPT.exists())
        shutil.copyfile(SCRIPT, scripts / SCRIPT.name)
        tip = self.commit('FABLE_SECRET')
        self.env['LEAK_SCAN_PATTERNS'] = str(self.patterns)
        result = subprocess.run(
            ['sh', str(ROOT / 'scripts/hooks/pre-push.sample'), 'example', 'unused-remote'],
            cwd=self.root, env=self.env, text=True, capture_output=True,
            input='refs/heads/new {} refs/heads/new {}\n'.format(tip, self.base))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('commit message line 1', result.stdout)
        self.assertNotIn('unused-remote', result.stdout + result.stderr)

    def test_sample_hook_startup_failures_print_a_fixed_line_without_paths(self):
        hook = str(ROOT / 'scripts/hooks/pre-push.sample')
        line = 'refs/heads/new {} refs/heads/new {}\n'.format(self.commit('ordinary'), self.base)
        fixed = 'ERROR leak-scan: scanner or python3 unavailable\n'

        def run(env):
            return subprocess.run(['sh', hook, 'example', 'unused-remote'], cwd=self.root, env=env,
                                  text=True, capture_output=True, input=line)

        missing = run(self.env)
        self.assertEqual((missing.returncode, missing.stdout, missing.stderr), (2, '', fixed))
        scripts = self.root / 'scripts'
        scripts.mkdir()
        shutil.copyfile(SCRIPT, scripts / SCRIPT.name)
        tools = self.root.parent / 'tools-without-python'
        tools.mkdir()
        for name in ('git', 'sh'):
            (tools / name).symlink_to(shutil.which(name))
        no_python = run(dict(self.env, PATH=str(tools)))
        self.assertEqual((no_python.returncode, no_python.stdout, no_python.stderr), (2, '', fixed))
        if os.geteuid() != 0:
            (scripts / SCRIPT.name).chmod(0)
            try:
                unreadable = run(self.env)
            finally:
                (scripts / SCRIPT.name).chmod(0o644)
            self.assertEqual((unreadable.returncode, unreadable.stdout, unreadable.stderr), (2, '', fixed))

    def test_environment_and_git_config_fallback_and_cli_precedence(self):
        self.git('config', 'leakscan.patterns', str(self.patterns))
        self.assertEqual(self.scan('--range', self.base + '..HEAD', patterns=False).returncode, 0)
        self.env['LEAK_SCAN_PATTERNS'] = str(self.patterns.parent / 'missing')
        self.assertEqual(self.scan('--range', self.base + '..HEAD', patterns=False).returncode, 2)
        self.assertEqual(self.scan('--range', self.base + '..HEAD').returncode, 0)

    def test_git_config_preserves_whitespace_in_private_filename(self):
        moved = self.patterns.with_name('patterns.txt ')
        self.patterns.rename(moved)
        self.patterns = moved
        self.git('config', 'leakscan.patterns', str(self.patterns))
        tip = self.commit('FABLE_SECRET')
        result = self.scan('--range', self.base + '..' + tip, patterns=False)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('pattern line 3', result.stdout)

    def test_git_errors_and_malformed_hook_input_fail_closed(self):
        for args, stdin in ((('--range', 'missing..HEAD'), None),
                            (('--range', 'HEAD...HEAD'), None), ((), 'malformed\n')):
            with self.subTest(args=args):
                result = self.scan(*args, stdin=stdin)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_existing_branch_hook_range(self):
        tip = self.commit('ordinary', {'new.txt': 'FABLE_SECRET\n'})
        result = self.scan(stdin='refs/heads/example {} refs/heads/example {}\n'.format(tip, self.base))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(tip, result.stdout)

    def test_new_branch_excludes_only_destination_remote_tracking_refs(self):
        self.commit('FABLE_SECRET already remote')
        remote = self.git('rev-parse', 'HEAD')
        self.git('update-ref', 'refs/remotes/origin/example', remote)
        tip = self.commit('ordinary')
        line = 'refs/heads/new {} refs/heads/new {}\n'.format(tip, '0' * 40)
        self.assertEqual(self.scan('origin', 'unused-remote', stdin=line).returncode, 0)
        self.git('update-ref', '-d', 'refs/remotes/origin/example')
        result = self.scan(stdin=line)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(remote, result.stdout)

    def load_scanner(self):
        spec = importlib.util.spec_from_file_location('leak_scan_fixture', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_changed_paths_are_scanned_and_private_paths_redacted(self):
        tip = self.commit('ordinary', {'FABLE_SECRET.txt': 'FABLE_SECRET\n'})
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('changed path line 1', result.stdout)
        self.assertIn('path [redacted] line 1', result.stdout)
        self.assertIn(tip, result.stdout)
        self.assertNotIn('FABLE_SECRET', result.stdout + result.stderr)

    def test_deleted_and_binary_paths_are_scanned(self):
        before = self.commit('ordinary', {'FABLE_SECRET.txt': 'ordinary\n'})
        self.git('rm', 'FABLE_SECRET.txt')
        tip = self.commit('ordinary', {'FABLE_SECRET.bin': b'\0ordinary'})
        result = self.scan('--range', before + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(result.stdout.count('changed path line 1'), 2)
        self.assertIn('binary skipped 1', result.stdout)
        self.assertNotIn('FABLE_SECRET', result.stdout + result.stderr)

    def test_hook_scans_local_and_destination_ref_names(self):
        for local, remote in (('FABLE_SECRET', 'safe'), ('safe', 'FABLE_SECRET')):
            with self.subTest(local=local):
                result = self.scan(stdin='refs/heads/{} {} refs/heads/{} {}\n'.format(
                    local, self.base, remote, self.base))
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn('ref name line 1', result.stdout)
                self.assertNotIn('FABLE_SECRET', result.stdout + result.stderr)

    def test_annotated_tag_message_and_tagger_identity_are_scanned(self):
        for number, field in enumerate(('message', 'name', 'email')):
            with self.subTest(field=field):
                if field != 'message':
                    self.env['GIT_COMMITTER_' + field.upper()] = 'FABLE_SECRET@example.invalid'
                self.git('-c', 'tag.gpgsign=false', 'tag', '-a', 'fixture-' + str(number),
                         '-m', 'FABLE_SECRET' if field == 'message' else 'ordinary')
                self.env.pop('GIT_COMMITTER_' + field.upper(), None)
                oid = self.git('rev-parse', 'fixture-' + str(number))
                result = self.scan(stdin='refs/tags/fixture-{} {} refs/tags/fixture-{} {}\n'.format(
                    number, oid, number, '0' * 40))
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn('tag ' + ('message' if field == 'message' else 'tagger ' + field), result.stdout)
                self.assertNotIn('FABLE_SECRET', result.stdout + result.stderr)

    def test_other_remotes_and_manual_scans_do_not_hide_commits(self):
        tip = self.commit('FABLE_SECRET')
        self.git('update-ref', 'refs/remotes/other/example', tip)
        line = 'refs/heads/new {} refs/heads/new {}\n'.format(tip, '0' * 40)
        for args in ((), ('origin', 'unused-remote')):
            with self.subTest(args=args):
                result = self.scan(*args, stdin=line)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(tip, result.stdout)

    def test_sample_hook_passes_destination_remote(self):
        scripts = self.root / 'scripts'
        scripts.mkdir()
        shutil.copyfile(SCRIPT, scripts / SCRIPT.name)
        tip = self.commit('FABLE_SECRET')
        self.git('update-ref', 'refs/remotes/destination/example', tip)
        self.env['LEAK_SCAN_PATTERNS'] = str(self.patterns)
        result = subprocess.run(['sh', str(ROOT / 'scripts/hooks/pre-push.sample'),
                                 'destination', 'unused-remote'], cwd=self.root,
                                env=self.env, text=True, capture_output=True,
                                input='refs/heads/new {} refs/heads/new {}\n'.format(tip, '0' * 40))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('CLEAN', result.stdout)

    def test_empty_patterns_and_empty_hook_input_refuse_clean(self):
        self.patterns.write_text('# comment\n  \n', encoding='utf-8')
        result = self.scan('--range', self.base + '..HEAD')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.patterns.write_text('FABLE_SECRET\n', encoding='utf-8')
        result = self.scan()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('nothing to scan', result.stderr)
        self.assertNotIn('CLEAN', result.stdout)

    def test_bom_and_trailing_pattern_whitespace_are_ignored(self):
        self.patterns.write_text('\ufeff# fixture\nFABLE_SECRET  \t\n', encoding='utf-8')
        tip = self.commit('FABLE_SECRET')
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn('FABLE_SECRET', result.stdout + result.stderr)

    def test_tip_only_range_scans_root_commit(self):
        self.patterns.write_text('ordinary\n', encoding='utf-8')
        result = self.scan('--range', self.base)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(self.base, result.stdout)

    def test_regex_compiler_failures_are_fixed_and_private(self):
        for pattern in ('FABLE_SECRET{999999999999999999999}', '(' * 2000 + 'FABLE_SECRET'):
            with self.subTest(pattern_length=len(pattern)):
                self.patterns.write_text(pattern, encoding='utf-8')
                result = self.scan('--range', self.base)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertEqual(result.stderr, 'ERROR leak-scan: invalid regex at pattern line 1\n')
                self.assertNotIn('FABLE_SECRET', result.stdout + result.stderr)

    def test_all_compiler_exceptions_and_unexpected_main_errors_are_sanitized(self):
        module = self.load_scanner()
        compile_regex = module.re.compile
        for error in (MemoryError, OverflowError, RecursionError, TypeError):
            with self.subTest(error=error.__name__):
                output = io.StringIO()
                with mock.patch.object(module, 'configured_patterns', return_value='unused'), \
                     mock.patch.object(module, 'git', return_value=b'/nonexistent-boundary'), \
                     mock.patch.object(module.Path, 'read_text', return_value='FABLE_SECRET'), \
                     mock.patch.object(module.re, 'compile', side_effect=lambda value, *a, **kw:
                         (_ for _ in ()).throw(error('FABLE_SECRET')) if value == 'FABLE_SECRET'
                         else compile_regex(value, *a, **kw)), \
                     redirect_stderr(output):
                    self.assertEqual(module.main([]), 2)
                self.assertEqual(output.getvalue(), 'ERROR leak-scan: invalid regex at pattern line 1\n')
        output = io.StringIO()
        with mock.patch.object(module, 'configured_patterns', side_effect=KeyError('FABLE_SECRET')), \
             redirect_stderr(output):
            self.assertEqual(module.main([]), 2)
        self.assertEqual(output.getvalue(), 'ERROR leak-scan: could not run\n')

    def test_git_ignores_replacements(self):
        tip = self.commit('ordinary', {'safe.txt': 'FABLE_SECRET\n'})
        original = self.git('rev-parse', 'HEAD:safe.txt')
        replacement = self.git('hash-object', '-w', '--stdin', input=b'ordinary\n')
        self.git('replace', original, replacement)
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('path "safe.txt"', result.stdout)

    def test_git_disables_lazy_fetch_for_every_invocation(self):
        module = self.load_scanner()
        with mock.patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess(
                [], 0, stdout=b'external-patterns\n', stderr=b'')) as run:
            module.git('rev-parse', 'HEAD')
            module.configured_patterns(None)
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(call.args[0][:2], ['git', '--no-replace-objects'])
            self.assertEqual(call.kwargs['env']['GIT_NO_LAZY_FETCH'], '1')

    def test_missing_blob_fails_closed(self):
        tip = self.commit('ordinary', {'safe.txt': 'FABLE_SECRET\n'})
        oid = self.git('rev-parse', 'HEAD:safe.txt')
        (self.root / '.git/objects' / oid[:2] / oid[2:]).unlink()
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn('CLEAN', result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    def test_hard_link_to_tracked_patterns_is_refused(self):
        self.commit('ordinary', {'patterns.txt': 'FABLE_SECRET\n'})
        self.patterns.unlink()
        os.link(self.root / 'patterns.txt', self.patterns)
        result = self.scan('--range', self.base + '..HEAD')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('outside the repository', result.stderr)

    def test_hard_link_guard_covers_tracked_files_outside_invocation_subdirectory(self):
        self.commit('ordinary', {'patterns.txt': 'FABLE_SECRET\n'})
        self.patterns.unlink()
        os.link(self.root / 'patterns.txt', self.patterns)
        child = self.root / 'child'
        child.mkdir()
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--patterns',
                                 str(self.patterns), '--range', 'HEAD..HEAD'],
                                cwd=child, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('outside the repository', result.stderr)

    def test_argument_errors_never_echo_private_text(self):
        result = self.scan('--FABLE_SECRET')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(result.stderr, 'ERROR leak-scan: invalid arguments\n')
        self.assertNotIn('FABLE_SECRET', result.stdout + result.stderr)

    def test_hook_git_lookup_disables_replacements_and_lazy_fetch(self):
        hook = (ROOT / 'scripts/hooks/pre-push.sample').read_text(encoding='utf-8')
        self.assertIn('GIT_NO_LAZY_FETCH=1 git --no-replace-objects rev-parse', hook)

    def test_case_alias_inside_repository_is_refused(self):
        internal = self.root / 'patterns.txt'
        internal.write_text('FABLE_SECRET\n', encoding='utf-8')
        alias = self.root.with_name('REPO') / 'patterns.txt'
        if not alias.exists():
            self.skipTest('case-sensitive filesystem')
        self.patterns = alias
        result = self.scan('--range', self.base + '..HEAD')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('outside the repository', result.stderr)

    def test_deleted_push_and_multiple_refs(self):
        deletion = '(delete) {} refs/heads/old {}\n'.format('0' * 40, self.base)
        self.assertEqual(self.scan(stdin=deletion).returncode, 0)
        tip = self.commit('FABLE_SECRET')
        line = 'refs/heads/new {} refs/heads/new {}\n'.format(tip, self.base)
        result = self.scan(stdin=deletion + line + line)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(result.stdout.count('commit message line 1'), 1)

    def test_merge_introduced_blob_and_odd_filenames(self):
        self.git('checkout', '-q', '-b', 'side')
        side = self.commit('side', {'side.txt': 'ordinary\n'})
        self.git('checkout', '-q', '-')
        self.commit('main', {'main.txt': 'ordinary\n'})
        self.git('merge', '--no-commit', '--no-ff', side)
        tip = self.commit('merge', {'odd\nname\t.txt': 'FABLE_SECRET\n'})
        result = self.scan('--range', self.base + '..' + tip)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(tip, result.stdout)
        self.assertIn('odd\\nname\\t.txt', result.stdout)


if __name__ == '__main__':
    unittest.main()
