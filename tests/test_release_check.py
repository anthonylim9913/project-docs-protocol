"""Release gate regressions; all repository fixtures live in temporary trees."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/release-check.py'


class ReleaseCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        for directory in ('scripts', 'docs', 'tests',
                          'staging/research-protocol/tests',
                          'staging/architect-protocol/tests'):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        for directory in ('tests', 'staging/research-protocol/tests',
                          'staging/architect-protocol/tests'):
            (self.root / directory / 'test_example.py').write_text(
                'import unittest\nclass Example(unittest.TestCase):\n'
                '    def test_example(self): self.assertTrue(True)\n', encoding='utf-8')
        (self.root / 'tests/__init__.py').write_text('', encoding='utf-8')
        for script in ('docs-doctor.py', 'skill-registry.py'):
            (self.root / 'scripts' / script).write_text(
                'print("PASS fixture")\n', encoding='utf-8')
        self.write('README.md', '**3 automated test methods**: 1 core, 1 research and 1 Architect.\n')
        self.write('docs/STATUS.md', 'Core 1 tests OK.\n')
        self.write('docs/CHANGELOG.md', '## Current\n\ncore 1, research 1, Architect 1.\n\n'
                   '## Historical\n\ncore 999 tests OK.\n')

    def write(self, path, text):
        (self.root / path).write_text(text, encoding='utf-8')

    def run_check(self, *args):
        self.assertTrue(SCRIPT.exists(), 'release-check.py has not been implemented')
        shutil.copyfile(SCRIPT, self.root / 'scripts/release-check.py')
        return subprocess.run([sys.executable, '-B', 'scripts/release-check.py', *args],
                              cwd=self.root, capture_output=True, text=True)

    def test_all_suites_and_current_counts_pass(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name in ('core', 'research', 'Architect', 'Doctor', 'skill-registry', 'git diff --check'):
            self.assertIn('PASS ' + name, result.stdout)
        self.assertIn('PASS release-check', result.stdout)

    def test_wrong_stated_count_names_file_and_line(self):
        self.write('README.md', 'core 999 tests\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('README.md:1', result.stdout)
        self.assertIn('stated 999; measured 1', result.stdout)

    def test_total_count_is_checked(self):
        self.write('README.md', '**9 automated test methods**: 1 core, 1 research and 1 Architect.\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('stated 9; measured 3', result.stdout)

    def test_status_and_only_newest_changelog_are_checked(self):
        for path in ('docs/STATUS.md', 'docs/CHANGELOG.md'):
            with self.subTest(path=path):
                old = (self.root / path).read_text(encoding='utf-8')
                self.write(path, '## Current\n\nresearch 8 tests\n')
                result = self.run_check()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(path + ':3', result.stdout)
                self.write(path, old)

    def test_unattributed_count_is_never_guessed(self):
        self.write('README.md', '27 fixture tests; 1 core tests.\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('not checked', result.stdout)
        self.assertIn('README.md:1', result.stdout)

    def test_doctor_warn_requires_explicit_override(self):
        self.write('scripts/docs-doctor.py', 'raise SystemExit(1)\n')
        for args, expected in (((), 1), (('--allow-doctor-warn',), 0)):
            result = self.run_check(*args)
            self.assertEqual(result.returncode, expected, result.stdout)
            self.assertIn('WARN Doctor', result.stdout)

    def test_doctor_fail_cannot_be_overridden(self):
        self.write('scripts/docs-doctor.py', 'raise SystemExit(2)\n')
        result = self.run_check('--allow-doctor-warn')
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('FAIL Doctor', result.stdout)

    def test_registry_failure_and_whitespace_failure_are_fatal(self):
        self.write('scripts/skill-registry.py', 'raise SystemExit(1)\n')
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        self.write('README.md', 'bad whitespace  \n')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('FAIL skill-registry', result.stdout)
        self.assertIn('FAIL git diff --check', result.stdout)

    def test_repeated_interpreters_each_run_three_suites(self):
        result = self.run_check('--python', sys.executable, '--python', sys.executable)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.count('PASS core'), 2)
        self.assertEqual(result.stdout.count('PASS research'), 2)
        self.assertEqual(result.stdout.count('PASS Architect'), 2)
        self.assertEqual(result.stdout.count('PASS Doctor'), 1)

    def test_missing_interpreter_fails_but_still_runs_checks(self):
        result = self.run_check('--python', str(self.root / 'absent-python'))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('FAIL core', result.stdout)
        self.assertIn('PASS Doctor', result.stdout)

    def test_failed_suite_or_missing_summary_cannot_pass(self):
        self.write('tests/test_example.py', 'raise RuntimeError("fixture failure")\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('FAIL core', result.stdout)
        self.write('tests/test_example.py', 'import os\nos._exit(0)\n')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('FAIL core', result.stdout)

    def test_skip_suites_is_explicitly_not_a_release_check(self):
        result = self.run_check('--skip-suites')
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn('not a release check', result.stdout)
        self.assertEqual(result.stdout.splitlines()[-1],
                         'INCOMPLETE release-check (suites skipped)')
        self.assertNotIn('PASS core', result.stdout)
        self.assertIn('not checked', result.stdout)

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def test_staged_whitespace_fails(self):
        self.write('bad.txt', 'bad whitespace  \n')
        self.git('add', '.')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('FAIL git diff --check --cached', result.stdout)

    def test_committed_whitespace_uses_explicit_base_or_newest_reachable_tag(self):
        base = self.commit()
        self.git('tag', 'fixture-base')
        self.write('bad.txt', 'bad whitespace  \n')
        self.commit()
        for args in ((), ('--base', base)):
            with self.subTest(args=args):
                result = self.run_check(*args)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn('FAIL committed whitespace', result.stdout)

    def test_no_reachable_tag_reports_committed_range_not_checked(self):
        self.commit()
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('INFO committed range not checked', result.stdout)

    def test_underscore_emphasis_is_checked(self):
        for label in ('_core_', '__core__'):
            with self.subTest(label=label):
                self.write('README.md', label + ' 999 tests\n')
                result = self.run_check()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn('stated 999; measured 1', result.stdout)

    def test_unattributed_counts_with_long_labels_and_partial_attribution_have_notice(self):
        for claim in ('27 very long descriptive fixture integration tests',
                      '1 core tests and 27 other very long fixture methods',
                      'tests: 27', 'the suite ran 27 checks as tests'):
            with self.subTest(claim=claim):
                self.write('README.md', claim + '\n')
                result = self.run_check()
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertIn('README.md:1: not checked', result.stdout)

    def test_zero_discovered_tests_fails(self):
        self.write('tests/test_example.py', '')
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('FAIL core', result.stdout)
        self.assertIn('0 tests; exit ', result.stdout)

    def test_missing_count_document_fails_closed(self):
        (self.root / 'README.md').unlink()
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('FAIL counts README.md', result.stdout)


if __name__ == '__main__':
    unittest.main()
