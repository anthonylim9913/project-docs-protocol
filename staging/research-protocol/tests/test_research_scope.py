"""Which folder the companion owns: the writer's explicit root and Doctor's signature."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import test_research_protocol as fixtures
DOCTOR, WRITE = fixtures.DOCTOR, fixtures.WRITE


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, '-B', str(script), *map(str, args)],
                          cwd=cwd, capture_output=True, text=True, timeout=10)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ResearchWriteScopeTests(unittest.TestCase):
    setUp = fixtures.ResearchProtocolTests.setUp
    tearDown = fixtures.ResearchProtocolTests.tearDown

    def write(self, spelling, expected, *extra, cwd=None):
        return run(WRITE, spelling, '# replacement\n', '--expected-sha256', expected, *extra, cwd=cwd)

    def assert_refused_unchanged(self, target, diagnostic, spellings):
        original = target.read_bytes(); listing = sorted(os.listdir(target.parent))
        for label, (spelling, extra, cwd) in spellings.items():
            with self.subTest(spelling=label):
                result = self.write(spelling, sha(target), *extra, cwd=cwd)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(diagnostic, result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                # Nothing written: same bytes and no lock or temp sidecar.
                self.assertEqual(target.read_bytes(), original)
                self.assertEqual(sorted(os.listdir(target.parent)), listing)

    def test_docs_research_target_rejected(self):
        target = self.root / 'docs/research/x.md'; target.parent.mkdir(parents=True); target.write_text('docs original\n')
        self.assert_refused_unchanged(target, 'inside research/', {
            'default root, relative': ('docs/research/x.md', (), self.root),
            'explicit root, absolute': (target, ('--root', self.root), None)})

    def test_other_research_folders_rejected(self):
        target = self.root / 'other/research/x.md'; target.parent.mkdir(parents=True); target.write_text('other original\n')
        self.assert_refused_unchanged(target, 'inside research/', {
            'default root': (target, (), self.root),
            'explicit root': (target, ('--root', self.root), None)})
        sibling = self.root / 'sibling'; (sibling / 'research').mkdir(parents=True)
        foreign = sibling / 'research/x.md'; foreign.write_text('sibling project original\n')
        self.assert_refused_unchanged(foreign, 'inside research/', {
            "another project's research/": (foreign, ('--root', self.root), None)})

    def test_symlinked_research_rejected(self):
        real = self.root / 'research-real'; (self.root / 'research').rename(real)
        (self.root / 'research').symlink_to(real, target_is_directory=True)
        target = real / 'notes/NOTE-0001.md'
        self.assert_refused_unchanged(target, 'symlinked research path: research', {
            'default root': ('research/notes/NOTE-0001.md', (), self.root),
            'explicit root': (self.root / 'research/notes/NOTE-0001.md', ('--root', self.root), None)})

    def test_default_root_is_the_current_directory(self):
        # Running from inside research/ no longer infers the project.
        target = self.root / 'research/notes/NOTE-0001.md'
        self.assert_refused_unchanged(target, 'inside research/', {
            'cwd research/notes': ('NOTE-0001.md', (), target.parent),
            'cwd research': ('notes/NOTE-0001.md', (), self.root / 'research')})

    def test_missing_root_rejected(self):
        target = self.root / 'research/notes/NOTE-0001.md'
        self.assert_refused_unchanged(target, 'project root not found', {
            'missing root': (target, ('--root', self.root / 'missing'), None)})

    def test_research_write_under_selected_root(self):
        target = self.root / 'research/notes/NOTE-0001.md'
        alias = Path(self.tmp.name + '-alias'); alias.symlink_to(self.root, target_is_directory=True)
        self.addCleanup(alias.unlink)
        cases = {'default root, relative': ('research/notes/NOTE-0001.md', (), self.root),
                 'explicit root, absolute': (target, ('--root', self.root), None),
                 'explicit root, cwd-relative': ('NOTE-0001.md', ('--root', self.root), target.parent),
                 'root reached through a trusted link': (alias / 'research/notes/NOTE-0001.md', ('--root', alias), None)}
        for label, (spelling, extra, cwd) in cases.items():
            with self.subTest(spelling=label):
                content = '# NOTE-0001 — ' + label + '\nSource: SRC-0001\n'
                result = run(WRITE, spelling, content, '--expected-sha256', sha(target), *extra, cwd=cwd)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('WROTE', result.stdout); self.assertEqual(target.read_text(), content)


class ResearchDoctorSignatureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'project'; (self.root / 'research').mkdir(parents=True)

    def skipped(self, reason):
        result = run(DOCTOR, self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout,
                         'SKIP research: research/ present but not a research-protocol folder (' + reason + ')\n')
        self.assertEqual(result.stderr, '')

    def test_empty_research_folder_is_skipped(self):
        self.skipped('no INDEX.md')

    def test_ordinary_notes_with_their_own_index_are_skipped(self):
        research = self.root / 'research'
        (research / '00-INDEX.md').write_text('# Reading list\n- paper one\n')
        (research / 'paper-notes.md').write_text('Notes on a paper.\n')
        (research / 'notes').mkdir(); (research / 'notes/meeting.md').write_text('# Meeting\n')
        self.skipped('no INDEX.md')
        # The exact name matters even on case-insensitive filesystems.
        (research / 'index.md').write_text('# Index\n')
        self.skipped('no INDEX.md')

    def test_index_without_stable_ids_is_skipped(self):
        (self.root / 'research/INDEX.md').write_text('# Reading list\n- paper one\n')
        self.skipped('INDEX.md has no stable IDs')

    def test_unrelated_virtualenv_links_are_never_inspected(self):
        outside = Path(self.tmp.name) / 'interpreter'; outside.write_text('outside')
        bin_dir = self.root / 'research/tool/.venv/bin'; bin_dir.mkdir(parents=True)
        (bin_dir / 'python').symlink_to(outside); (self.root / 'research/tool/main.py').write_text('print(1)\n')
        self.skipped('no INDEX.md')

    def test_help_says_absence_is_valid(self):
        result = run(DOCTOR, '--help')
        self.assertEqual(result.returncode, 0); self.assertIn('Absence is valid', ' '.join(result.stdout.split()))

    def test_shipped_example_passes(self):
        result = run(DOCTOR, fixtures.ROOT / 'examples/conflicting-evidence')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PASS research-index: 6 records', result.stdout)


class ResearchDoctorCompanionTests(unittest.TestCase):
    """With the signature present every existing check still applies."""
    setUp = fixtures.ResearchProtocolTests.setUp
    tearDown = fixtures.ResearchProtocolTests.tearDown

    def failed(self, diagnostic):
        result = run(DOCTOR, self.root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(diagnostic, result.stdout); self.assertNotIn('SKIP', result.stdout)

    def test_index_missing_one_record_fails(self):
        index = self.root / 'research/INDEX.md'
        # The RQ line still cites NOTE-0001, so its entry is unresolved.
        index.write_text(index.read_text().replace('- NOTE-0001 — `notes/NOTE-0001.md`\n', ''))
        self.failed('FAIL NOTE-0001 has unresolved INDEX.md link')

    def test_records_without_index_fail(self):
        (self.root / 'research/INDEX.md').unlink()
        self.failed('FAIL research-index: INDEX.md missing')

    def test_symlink_refusal_kept_inside_companion(self):
        outside = self.root / 'interpreter'; outside.write_text('outside')
        bin_dir = self.root / 'research/tool/.venv/bin'; bin_dir.mkdir(parents=True)
        (bin_dir / 'python').symlink_to(outside)
        self.failed('FAIL symlinked research path: python')


if __name__ == '__main__':
    unittest.main()
