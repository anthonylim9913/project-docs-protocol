"""LG-0044(b): the judging code is verified, isolated and loaded from verified bytes before it judges.

Each case starts from a passing complete packet in a disposable committed copy and changes the
harness or the interpreter's view of it (never the packet's evidence about the product). The
change must be refused rather than approved by the changed code itself.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests import input_manifest
from tests.acceptance_support import ROOT, copy_subject, commit, generate, invoke, invoke_isolated, MANIFEST

VALIDATOR = 'tests/validate_acceptance.py'


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='harness binding ')
        cls.directory = Path(cls.temp.name)
        cls.root = cls.directory / 'subject'
        copy_subject(cls.root)
        cls.packet, cls.hashes = generate(cls.root, cls.directory)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def run_validator(self, packet=None, *extra, root=None, hashes=None, isolated=True, flags=()):
        root = root or self.root
        path = self.directory / 'packet.json'
        path.write_text(json.dumps(self.packet if packet is None else packet))
        command = [sys.executable, *(('-I',) if isolated else ()), *flags, '-B', str(root / VALIDATOR), *extra,
                   str(path), str(root / MANIFEST), str(hashes or self.hashes)]
        return subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60)

    def edited(self, name, transform, root=None):
        target = (root or self.root) / name
        original = target.read_bytes()
        self.addCleanup(target.write_bytes, original)
        target.write_bytes(transform(original))
        return original

    def refused(self, p, diagnostic):
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn(diagnostic, p.stderr)
        self.assertNotIn('Traceback', p.stderr)
        self.assertNotIn('"accepted"', p.stdout)


class HarnessRecordTests(Base):
    def test_control_unchanged_harness_is_accepted(self):
        p = self.run_validator()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout), {'accepted': True, 'cases': 4})

    def test_validator_edited_to_skip_canonical_checks_cannot_approve_itself(self):
        forged = copy.deepcopy(self.packet)
        forged.pop('evidence_scope')
        control = self.run_validator(forged)
        self.refused(control, 'canonical evidence scope')
        self.edited(VALIDATOR, lambda b: b.replace(b'strict=True)', b'strict=False)', 1))
        p = self.run_validator(forged)
        self.assertEqual(p.returncode, 1, 'edited validator approved its own run: ' + p.stdout)
        self.assertIn('harness digest does not match', p.stderr)

    def test_one_byte_change_to_each_judging_file_or_input_is_rejected(self):
        self.assertGreaterEqual(len(input_manifest.HARNESS_FILES), 17)
        for name in input_manifest.HARNESS_FILES:
            with self.subTest(name=name):
                saved = self.edited(name, lambda b: b + b' ')
                self.refused(self.run_validator(), 'harness digest does not match')
                (self.root / name).write_bytes(saved)

    def test_deleted_judging_file_is_rejected_not_a_crash(self):
        for name in input_manifest.HARNESS_FILES:
            if name == VALIDATOR:
                continue  # a deleted validator cannot be started, let alone approve anything
            with self.subTest(name=name):
                target = self.root / name
                saved = target.read_bytes()
                target.unlink()
                try:
                    self.refused(self.run_validator(), 'harness file missing')
                finally:
                    target.write_bytes(saved)

    def test_record_missing_altered_or_with_wrong_scope_is_rejected(self):
        record = self.root / input_manifest.HARNESS_RECORD
        original = record.read_bytes()
        self.addCleanup(record.write_bytes, original)
        lines = original.decode().splitlines(keepends=True)
        for label, content in (('altered digest', ('0' * 64).join([lines[0][:lines[0].index(':') + 1], '\n']) + ''.join(lines[1:])),
                               ('dropped line', ''.join(lines[1:])),
                               ('extra line', original.decode() + 'tests/extra.py:' + '0' * 64 + '\n'),
                               ('unsorted', ''.join(reversed(lines))),
                               ('empty', ''), ('no final newline', original.decode().rstrip('\n'))):
            with self.subTest(label=label):
                record.write_text(content)
                p = self.run_validator()
                self.assertEqual(p.returncode, 1, p.stdout)
                self.assertIn('harness digest', p.stderr)
        record.unlink()
        self.refused(self.run_validator(), 'harness digest record missing')

    def test_reviewer_pin_must_match_the_running_harness(self):
        digest = input_manifest.harness_digest(self.root)
        self.assertEqual(digest, hashlib.sha256((self.root / input_manifest.HARNESS_RECORD).read_bytes()).hexdigest())
        self.assertEqual(self.run_validator(None, '--harness-sha256', digest).returncode, 0)
        for bad in ('0' * 64, 'not-a-digest', digest.upper()):
            with self.subTest(pin=bad):
                self.refused(self.run_validator(None, '--harness-sha256', bad), 'reviewer pin')

    def test_pin_without_value_is_a_usage_error(self):
        self.assertEqual(self.run_validator(None, '--harness-sha256').returncode, 2)

    def test_record_is_current_and_not_part_of_its_own_digest(self):
        self.assertNotIn(input_manifest.HARNESS_RECORD, input_manifest.HARNESS_FILES)
        self.assertEqual((ROOT / input_manifest.HARNESS_RECORD).read_text(), input_manifest.harness_record_text(ROOT))

    def test_digest_commands_agree_with_the_record(self):
        p = invoke(self.root, VALIDATOR.replace('validate_acceptance', 'input_manifest'), self.root, '--print-harness-digest')
        self.assertEqual(p.stdout.strip(), hashlib.sha256((self.root / input_manifest.HARNESS_RECORD).read_bytes()).hexdigest())
        record = self.root / input_manifest.HARNESS_RECORD
        saved = record.read_bytes()
        self.addCleanup(record.write_bytes, saved)
        record.write_text('')
        self.assertEqual(invoke(self.root, 'tests/input_manifest.py', self.root, '--write-harness-record').returncode, 0)
        self.assertEqual(record.read_bytes(), saved)

    def test_harness_files_and_record_are_inside_the_bound_input_scope(self):
        bound = set(json.loads(self.hashes.read_text()))
        self.assertLessEqual(set(input_manifest.HARNESS_FILES) | {input_manifest.HARNESS_RECORD}, bound)

    def test_validator_required_files_equal_the_manifest_module_list(self):
        text = (self.root / VALIDATOR).read_text()
        namespace = {}
        start = text.index('MODULE_FILES = ')
        end = text.index('M = types.SimpleNamespace')
        exec(text[start:end], namespace)
        self.assertEqual(set(namespace['HARNESS_PATHS']), set(input_manifest.HARNESS_FILES))


class IsolationTests(Base):
    def test_not_isolated_or_writing_bytecode_is_refused(self):
        self.refused(self.run_validator(isolated=False), 'run isolated')
        # -I without -B: bytecode caches could then appear beside the judging code
        command = [sys.executable, '-I', str(self.root / VALIDATOR)]
        p = subprocess.run(command, cwd=self.root, capture_output=True, text=True, timeout=60,
                           env={'PYTHONDONTWRITEBYTECODE': ''})
        self.assertEqual(p.returncode, 2)  # usage first: no arguments
        path = self.directory / 'packet.json'
        path.write_text(json.dumps(self.packet))
        p = subprocess.run(command[:2] + [str(self.root / VALIDATOR), str(path), str(self.root / MANIFEST), str(self.hashes)],
                           cwd=self.root, capture_output=True, text=True, timeout=60, env={})
        self.refused(p, 'run isolated')

    def poisoned(self, *, plant=None, entry=True):
        """Run the validator after putting a directory of the reviewed tree first on sys.path."""
        planted = self.root / 'tests' / 'hashlib.py'
        if plant:
            planted.write_text(plant)
            self.addCleanup(lambda: planted.exists() and planted.unlink())
        code = ("import sys, runpy\n"
                f"{'sys.path.insert(0, %r)' % str(self.root / 'tests') if entry else ''}\n"
                f"sys.argv = ['validate_acceptance.py', {str(self.directory / 'packet.json')!r}, "
                f"{str(self.root / MANIFEST)!r}, {str(self.hashes)!r}]\n"
                f"runpy.run_path({str(self.root / VALIDATOR)!r}, run_name='__main__')\n")
        (self.directory / 'packet.json').write_text(json.dumps(self.packet))
        return subprocess.run([sys.executable, '-I', '-B', '-c', code], cwd=self.root,
                              capture_output=True, text=True, timeout=60)

    def test_control_without_poisoned_path_is_accepted(self):
        p = self.poisoned(entry=False)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_search_path_entry_inside_the_tree_is_refused(self):
        self.refused(self.poisoned(), 'search path entry inside the reviewed tree')

    def test_planted_stdlib_module_is_refused(self):
        shadow = ("import os, sysconfig\n"
                  "exec(compile(open(os.path.join(sysconfig.get_path('stdlib'), 'hashlib.py')).read(), 'hashlib.py', 'exec'))\n")
        p = self.poisoned(plant=shadow)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertNotIn('"accepted"', p.stdout)
        self.assertRegex(p.stderr, 'standard-library module shadowed|search path entry inside')

    def test_bytecode_and_import_hooks_in_the_tree_are_refused(self):
        for name in ('tests/__pycache__/x.cpython-311.pyc', 'scripts/a.pyc', 'tests/a.pyo', 'tests/a.so',
                     'scripts/a.pyd', 'a.pth', 'tests/.tmp/hidden.pyc', 'staging/research-protocol/scripts/__pycache__/n.txt'):
            with self.subTest(name=name):
                path = self.root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'\0')
                self.addCleanup(lambda p=path: p.exists() and p.unlink())
                self.refused(self.run_validator(), 'bytecode or import hook')
                m = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.directory / 'o.json')
                self.assertEqual(m.returncode, 2, m.stdout + m.stderr)
                self.assertIn('bytecode or import hook', m.stderr)
                path.unlink()

    def test_ignored_operating_system_litter_does_not_block_a_clean_tree(self):
        for name in ('.DS_Store', 'tests/.DS_Store', 'docs/.DS_Store'):
            path = self.root / name
            path.write_bytes(b'\0')
            self.addCleanup(lambda p=path: p.exists() and p.unlink())
        m = invoke(self.root, 'tests/input_manifest.py', self.root, '--out', self.directory / 'ds.json')
        self.assertEqual(m.returncode, 0, m.stderr)
        self.assertFalse([n for n in json.loads((self.directory / 'ds.json').read_text())['files'] if n.endswith('.DS_Store')])
        self.assertEqual(self.run_validator().returncode, 0)


class RunnerTests(Base):
    def test_runner_prints_no_verdict_when_the_harness_differs_from_its_record(self):
        name = 'tests/fixtures/acceptance-v2/contract.json'
        self.edited(name, lambda b: b + b' ')
        result = self.directory / 'runner-result.json'
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.root, text=True).strip()
        p = invoke(self.root, 'tests/run_acceptance.py', '--runtime-root', self.root, '--result', result,
                   '--source-commit', head)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertNotIn('accepted', p.stdout)
        self.assertIn('harness digest does not match', json.loads(result.read_text())['failures'][0]['message'])


class AuditTests(Base):
    def test_every_file_the_verdict_reads_is_pinned(self):
        out = self.directory / 'opened.json'
        code = ("import sys, runpy, json\n"
                "opened = set()\n"
                "def hook(event, args):\n"
                "    if event != 'open' or not isinstance(args[0], str): return\n"
                "    frame = sys._getframe(1)\n"
                "    while frame:\n"
                "        if frame.f_code.co_name in ('hashes', 'committed_hashes'): return\n"
                "        frame = frame.f_back\n"
                "    opened.add(args[0])\n"
                "sys.addaudithook(hook)\n"
                f"sys.argv = ['validate_acceptance.py', {str(self.directory / 'packet.json')!r}, "
                f"{str(self.root / MANIFEST)!r}, {str(self.hashes)!r}]\n"
                "try:\n"
                f"    runpy.run_path({str(self.root / VALIDATOR)!r}, run_name='__main__')\n"
                "except SystemExit as e:\n"
                "    code = e.code\n"
                f"json.dump(sorted(opened), open({str(out)!r}, 'w'))\n")
        (self.directory / 'packet.json').write_text(json.dumps(self.packet))
        p = subprocess.run([sys.executable, '-I', '-B', '-c', code], cwd=self.root, capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        root = str(self.root.resolve()) + '/'
        inside = {n[len(root):] for n in json.loads(out.read_text()) if str(Path(n).resolve()).startswith(root)}
        pinned = set(input_manifest.HARNESS_FILES) | {input_manifest.HARNESS_RECORD}
        self.assertEqual(inside - pinned, set(), 'the verdict read files that the harness digest does not cover')
        self.assertLessEqual({'tests/fixtures/acceptance-v2/contract.json', 'templates/LEDGER.md'}, inside)


class ExternalJudgeTests(unittest.TestCase):
    """A trusted checkout's validator judges a separate candidate tree."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='external judge ')
        cls.directory = Path(cls.temp.name)
        cls.judge = cls.directory / 'trusted'
        cls.candidate = cls.directory / 'candidate'
        for root in (cls.judge, cls.candidate):
            copy_subject(root)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def judge_candidate(self, packet, hashes, *extra):
        path = self.directory / 'candidate-packet.json'
        path.write_text(json.dumps(packet))
        return subprocess.run([sys.executable, '-I', '-B', str(self.judge / VALIDATOR), '--subject-root',
                               str(self.candidate), *extra, str(path), str(self.judge / MANIFEST), str(hashes)],
                              cwd=self.judge, capture_output=True, text=True, timeout=60)

    def test_candidate_with_edited_validator_cannot_approve_a_forged_packet(self):
        packet, hashes = generate(self.candidate, self.directory)
        honest = self.judge_candidate(packet, hashes)
        self.assertEqual(honest.returncode, 0, honest.stderr)
        report = json.loads(honest.stdout)
        self.assertTrue(report['candidate_harness_matches_judge'])
        validator = self.candidate / VALIDATOR
        original = validator.read_bytes()
        self.addCleanup(lambda: (validator.write_bytes(original), input_manifest.write_harness_record(self.candidate),
                                 commit(self.candidate)))
        validator.write_bytes(original.replace(b'strict=True)', b'strict=False)', 1))
        # a coordinated edit: the candidate re-records its own digest, as an honest change would
        input_manifest.write_harness_record(self.candidate)
        commit(self.candidate)
        packet, hashes = generate(self.candidate, self.directory)
        forged = copy.deepcopy(packet)
        forged.pop('evidence_scope')
        # the limit of an in-tree record: the coordinated candidate validator approves the forgery...
        (self.directory / 'forged.json').write_text(json.dumps(forged))
        own = subprocess.run([sys.executable, '-I', '-B', str(validator), str(self.directory / 'forged.json'),
                              str(self.candidate / MANIFEST), str(hashes)], cwd=self.candidate, capture_output=True, text=True)
        self.assertEqual(own.returncode, 0, own.stderr)
        # ...which is why the trusted checkout judges it instead
        refused = self.judge_candidate(forged, hashes)
        self.assertEqual(refused.returncode, 1, refused.stdout)
        self.assertIn('canonical evidence scope', refused.stderr)
        # a packet that is honest about the edited candidate is reported as a different harness
        ok = self.judge_candidate(packet, hashes)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertFalse(json.loads(ok.stdout)['candidate_harness_matches_judge'])
        pinned = self.judge_candidate(packet, hashes, '--candidate-harness-sha256',
                                      input_manifest.harness_digest(self.judge))
        self.assertEqual(pinned.returncode, 1)
        self.assertIn('candidate harness digest', pinned.stderr)


if __name__ == '__main__':
    unittest.main()
