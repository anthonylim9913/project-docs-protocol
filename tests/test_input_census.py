"""Fail-closed census controls, including real permission-denied walks."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests import input_manifest
from tests.acceptance_support import copy_subject, invoke


class InputCensusTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='input-census-')
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / 'subject'
        with patch.dict(os.environ, {'GIT_CONFIG_COUNT': '2',
                                     'GIT_CONFIG_KEY_0': 'gc.auto', 'GIT_CONFIG_VALUE_0': '0',
                                     'GIT_CONFIG_KEY_1': 'maintenance.auto', 'GIT_CONFIG_VALUE_1': 'false'}):
            copy_subject(self.root)
        self.out = self.directory / 'manifest.json'

    def make_unreadable(self, path):
        previous = path.stat().st_mode
        path.chmod(0)
        self.addCleanup(path.chmod, previous)
        if os.access(path, os.R_OK):
            self.skipTest('permission denial requires an unprivileged user')

    def test_unreadable_untracked_normative_directory_exits_two(self):
        directory = self.root / 'normative'
        directory.mkdir()
        (directory / 'RULES.md').write_text('# Normative rules\n')
        self.make_unreadable(directory)
        result = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.out)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('cannot enumerate: ' + str(directory.resolve()), result.stderr)
        self.assertFalse(self.out.exists())

    def test_unreadable_untracked_file_exits_two_and_names_path(self):
        target = self.root / 'UNTRACKED.md'
        target.write_text('# Unreadable rule\n')
        self.make_unreadable(target)
        result = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.out)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('UNTRACKED.md', result.stderr)
        self.assertFalse(self.out.exists())

    def test_unreadable_excluded_directory_is_not_descended_into(self):
        directory = self.root / 'tests/.tmp'
        directory.mkdir(exist_ok=True)
        (directory / 'RULES.md').write_text('excluded scratch\n')
        self.make_unreadable(directory)
        result = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.out)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('tests/.tmp/RULES.md', json.loads(self.out.read_text())['files'])

    def test_git_errors_and_stderr_fail_closed_for_every_operation(self):
        real_run = subprocess.run
        for operation in ('ls-tree', 'diff', 'cat-file', 'rev-parse'):
            for returncode, stderr in ((0, b'inventory warning\n'), (1, b'')):
                with self.subTest(operation=operation, returncode=returncode):
                    seen = []

                    def run(command, **kwargs):
                        if operation in command:
                            seen.append(kwargs)
                            result = real_run(command, **kwargs)
                            result.returncode = returncode
                            result.stderr = stderr.decode() if kwargs.get('text') else stderr
                            return result
                        return real_run(command, **kwargs)

                    errors = io.StringIO()
                    with patch.object(input_manifest.subprocess, 'run', side_effect=run), \
                            patch.object(sys, 'argv', ['input_manifest.py', str(self.root), '--out', str(self.out)]), \
                            contextlib.redirect_stderr(errors):
                        with self.assertRaises(SystemExit) as raised:
                            input_manifest.main()
                    self.assertEqual(raised.exception.code, 2)
                    self.assertTrue(seen)
                    self.assertTrue(all(options.get('capture_output') for options in seen))
                    self.assertIn('git', errors.getvalue())
                    self.assertFalse(self.out.exists())

    def test_nested_git_directory_is_pruned_but_other_hidden_inputs_are_not(self):
        nested = self.root / 'extras/.git'
        nested.mkdir(parents=True)
        self.make_unreadable(nested)
        (self.root / '.hidden-rule').write_text('new input\n')
        result = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.out)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('.hidden-rule', result.stderr)


if __name__ == '__main__':
    unittest.main()
