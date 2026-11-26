"""Privacy scanner tests use only invented secrets and disposable Git history."""
import os
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
                            (('--range', 'HEAD'), None), ((), 'malformed\n')):
            with self.subTest(args=args):
                result = self.scan(*args, stdin=stdin)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_existing_branch_hook_range(self):
        tip = self.commit('ordinary', {'new.txt': 'FABLE_SECRET\n'})
        result = self.scan(stdin='refs/heads/example {} refs/heads/example {}\n'.format(tip, self.base))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(tip, result.stdout)

    def test_new_branch_excludes_every_remote_tracking_ref(self):
        self.commit('FABLE_SECRET already remote')
        remote = self.git('rev-parse', 'HEAD')
        self.git('update-ref', 'refs/remotes/origin/example', remote)
        tip = self.commit('ordinary')
        line = 'refs/heads/new {} refs/heads/new {}\n'.format(tip, '0' * 40)
        self.assertEqual(self.scan(stdin=line).returncode, 0)
        self.git('update-ref', '-d', 'refs/remotes/origin/example')
        result = self.scan(stdin=line)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(remote, result.stdout)

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
