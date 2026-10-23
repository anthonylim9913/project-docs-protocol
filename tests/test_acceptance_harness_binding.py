"""LG-0044(b): the judging code is verified, loaded from verified bytes, and can be external.

Each case starts from a passing complete packet in a disposable committed copy,
changes the harness or plants code beside it (never the packet's evidence of the
product), and shows the change is refused instead of being approved by the
changed code itself. The external cases use one unmodified copy as the trusted
checkout and judge a separate candidate copy (D-0025).
"""
import hashlib
import json
from pathlib import Path
import py_compile
import sys
import tempfile
import textwrap
import unittest
from tests import input_manifest
from tests.acceptance_support import (ROOT, MANIFEST, commit, copy_subject, external, generate,
                                      invoke, isolated)

VALIDATOR = 'tests/validate_acceptance.py'
RUNNER = 'tests/run_acceptance.py'


def forged(packet):
    """A packet the real gate rejects ('canonical evidence scope'), for a planted gate to approve."""
    packet = json.loads(json.dumps(packet))
    packet.pop('evidence_scope')
    return packet


class HarnessBindingTests(unittest.TestCase):
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

    def run_validator(self, packet=None, *extra, root=None):
        root = root or self.root
        path = self.directory / 'packet.json'
        path.write_text(json.dumps(self.packet if packet is None else packet))
        return invoke(root, VALIDATOR, *extra, path, MANIFEST, self.hashes)

    def edited(self, name, transform, root=None):
        target = (root or self.root) / name
        original = target.read_bytes()
        self.addCleanup(target.write_bytes, original)
        target.write_bytes(transform(original))

    def candidate(self):
        """A separate committed copy, for cases that commit or judge across checkouts."""
        temp = tempfile.TemporaryDirectory(prefix='harness candidate ')
        self.addCleanup(temp.cleanup)
        directory = Path(temp.name)
        root = directory / 'candidate'
        copy_subject(root)
        return root, directory

    def assert_reject(self, process, diagnostic):
        self.assertEqual(process.returncode, 1, process.stdout + process.stderr)
        self.assertIn('REJECT: ' + diagnostic, process.stderr)
        self.assertNotIn('"accepted"', process.stdout)
        self.assertNotIn('Traceback', process.stderr)

    # Record, pin and digest ------------------------------------------------------------

    def test_control_unchanged_harness_is_accepted(self):
        p = self.run_validator()
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_control_runs_isolated(self):
        path = self.directory / 'packet.json'
        path.write_text(json.dumps(self.packet))
        p = isolated(self.root, VALIDATOR, path, MANIFEST, self.hashes)
        self.assertEqual((p.returncode, json.loads(p.stdout or '{}')), (0, {'accepted': True, 'cases': 4}), p.stderr)

    def test_validator_edited_to_skip_canonical_checks_cannot_approve_itself(self):
        control = self.run_validator(forged(self.packet))
        self.assert_reject(control, 'canonical evidence scope')
        self.edited(VALIDATOR, lambda b: b.replace(b'strict=True,', b'strict=False,', 1))
        self.assertNotEqual(self.root.joinpath(VALIDATOR).read_bytes(), b'')
        p = self.run_validator(forged(self.packet))
        self.assertEqual(p.returncode, 1, 'edited validator approved its own run: ' + p.stdout)
        self.assertIn('harness files do not match', p.stderr)

    def test_one_byte_change_to_each_harness_file_is_rejected(self):
        self.assertGreaterEqual(len(input_manifest.HARNESS_FILES), 17)
        for name in input_manifest.HARNESS_FILES:
            with self.subTest(name=name):
                target = self.root / name
                saved = target.read_bytes()
                try:
                    target.write_bytes(saved + b' ')
                    self.assert_reject(self.run_validator(), 'harness files do not match tests/harness.sha256: ' + name)
                finally:
                    target.write_bytes(saved)

    def test_harness_module_deleted_is_a_clean_reject(self):
        for name in ('tests/acceptance_gate.py', 'tests/input_manifest.py',
                     'tests/fixtures/hardening-2026-09-12/acceptance-cases.json',
                     'tests/fixtures/acceptance-v2/contract.json'):
            with self.subTest(name=name):
                target = self.root / name
                saved = target.read_bytes()
                try:
                    target.unlink()
                    self.assert_reject(self.run_validator(), 'harness file missing or unreadable: ' + name)
                finally:
                    target.write_bytes(saved)

    def test_record_missing_altered_malformed_or_short_is_rejected(self):
        record = self.root / input_manifest.HARNESS_RECORD
        original = record.read_text()
        self.addCleanup(record.write_text, original)
        first = original.splitlines()[0]
        record.write_text(original.replace(first, '0' * 64 + first[64:]))
        self.assert_reject(self.run_validator(), 'harness files do not match')
        record.write_text('0' * 64 + '\n')
        self.assert_reject(self.run_validator(), 'harness record is malformed')
        record.write_text(''.join(line + '\n' for line in original.splitlines()
                                  if not line.endswith('  tests/fixtures/acceptance-v2/contract.json')))
        self.assert_reject(self.run_validator(), 'harness record omits judging files: tests/fixtures/acceptance-v2/contract.json')
        record.unlink()
        self.assert_reject(self.run_validator(), 'harness record missing')

    def test_reviewer_pin_must_match_the_record(self):
        digest = hashlib.sha256((self.root / input_manifest.HARNESS_RECORD).read_bytes()).hexdigest()
        for form in (('--harness-sha256', digest), ('--harness-sha256=' + digest,)):
            with self.subTest(form=form[0][:17]):
                ok = self.run_validator(None, *form)
                self.assertEqual(ok.returncode, 0, ok.stderr)
        for bad in ('0' * 64, 'not-a-digest', digest.upper()):
            with self.subTest(pin=bad):
                self.assert_reject(self.run_validator(None, '--harness-sha256', bad), 'harness record does not match the reviewer pin')

    def test_pin_without_value_is_a_usage_error(self):
        path = self.directory / 'packet.json'
        p = invoke(self.root, VALIDATOR, path, MANIFEST, self.hashes, '--harness-sha256')
        self.assertEqual(p.returncode, 2)
        self.assertIn('usage:', p.stderr)

    def test_record_is_current_and_lists_exactly_the_harness(self):
        recorded = (ROOT / input_manifest.HARNESS_RECORD).read_text()
        self.assertEqual(recorded, input_manifest.harness_record(ROOT))
        names = [line.split('  ', 1)[1] for line in recorded.splitlines()]
        self.assertEqual(names, sorted(input_manifest.HARNESS_FILES))
        self.assertNotIn(input_manifest.HARNESS_RECORD, names)

    def test_digest_command_prints_what_a_reviewer_pins(self):
        p = invoke(self.root, 'tests/input_manifest.py', self.root, '--print-harness-digest')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.strip(), hashlib.sha256((self.root / input_manifest.HARNESS_RECORD).read_bytes()).hexdigest())

    def test_harness_files_are_inside_the_bound_input_scope(self):
        bound = set(json.loads(self.hashes.read_text()))
        self.assertLessEqual(set(input_manifest.HARNESS_FILES) | {input_manifest.HARNESS_RECORD}, bound)

    # R1: code planted beside the harness -------------------------------------------------

    def planted(self, files, committed=True):
        root, directory = self.candidate()
        packet, hashes = generate(root, directory)
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content) if isinstance(content, bytes) else path.write_text(content)
        if committed:
            commit(root)
        path = directory / 'forged.json'
        path.write_text(json.dumps(forged(packet)))
        return root, invoke(root, VALIDATOR, path, MANIFEST, hashes)

    def test_shadowing_package_is_refused(self):
        # A package beside the module wins the import; it approves everything.
        _, p = self.planted({'tests/acceptance_gate/__init__.py': textwrap.dedent('''\
            class GateError(ValueError):
                pass
            def validate_json(*args, **kwargs):
                return {"accepted": True, "cases": 4}
            def validate_result(*args, **kwargs):
                return None
            ''')})
        self.assert_reject(p, 'module or bytecode in tests/ could shadow the harness: tests/acceptance_gate')

    def test_stdlib_named_module_in_tests_is_refused(self):
        _, p = self.planted({'tests/json.py': 'import sys\nprint(\'{"accepted": true, "cases": 4}\')\nsys.exit(0)\n'})
        self.assert_reject(p, 'module or bytecode in tests/ could shadow the harness: tests/json.py')

    def test_planted_bytecode_is_refused_tracked_or_not(self):
        for committed in (False, True):
            with self.subTest(committed=committed):
                with tempfile.TemporaryDirectory() as scratch:
                    source = Path(scratch) / 'acceptance_gate.py'
                    source.write_text((ROOT / 'tests/acceptance_gate.py').read_text().replace(
                        'validate_result(result, expected_cases, runtime_hashes, strict=strict, subject_root=subject_root)\n    return',
                        'return'))
                    cfile = Path(scratch) / 'gate.pyc'
                    py_compile.compile(str(source), cfile=str(cfile),
                                       invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
                    name = 'tests/__pycache__/acceptance_gate.%s.pyc' % sys.implementation.cache_tag
                    _, p = self.planted({name: cfile.read_bytes()}, committed)
                self.assert_reject(p, 'module or bytecode in tests/ could shadow the harness: tests/__pycache__')

    def test_module_from_an_unexpected_path_is_refused_after_loading(self):
        probe = textwrap.dedent('''\
            import sys, types
            from pathlib import Path
            root = Path(sys.argv[1])
            path = root / "tests/validate_acceptance.py"
            boot = types.ModuleType("validate_acceptance"); boot.__file__ = str(path)
            exec(compile(path.read_bytes(), str(path), "exec"), boot.__dict__)
            stray = types.ModuleType("helper"); stray.__file__ = str(root / "tests/helper.py")
            sys.modules["helper"] = stray
            try:
                boot.load_harness(root)
            except boot.HarnessError as error:
                print(error)
            ''')
        script = self.directory / 'probe.py'
        script.write_text(probe)
        p = isolated(self.directory, script, self.root)
        self.assertIn('module helper was loaded from an unexpected path', p.stdout, p.stderr)

    # R3: everything the verdict reads is in the harness ---------------------------------

    def test_files_the_verdict_reads_are_exactly_the_harness(self):
        """Audit `open` in the trusted checkout while its runner and validator judge a candidate."""
        candidate, directory = self.candidate()
        audit = directory / 'audit.py'
        audit.write_text(textwrap.dedent('''\
            import runpy, sys
            from pathlib import Path
            trusted, log, script = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
            opened = set()
            def hook(event, args):
                if event == "open" and isinstance(args[0], str):
                    path = Path(args[0]).resolve()
                    if trusted in path.parents:
                        opened.add(path.relative_to(trusted).as_posix())
            sys.addaudithook(hook)
            sys.argv = [str(trusted / script)] + sys.argv[4:]
            try:
                runpy.run_path(sys.argv[0], run_name="__main__")
            finally:
                open(log, "w").write("\\n".join(sorted(opened)))
            '''))
        head = commit(candidate)
        result, hashes = directory / 'result.json', directory / 'hashes.json'
        hashes.write_text(json.dumps(input_manifest.hashes(candidate)))
        expected = set(input_manifest.HARNESS_FILES) | {input_manifest.HARNESS_RECORD}
        for script, args in ((RUNNER, ['--runtime-root', candidate, '--result', result, '--source-commit', head]),
                             (VALIDATOR, ['--subject-root', candidate, result, self.root / MANIFEST, hashes])):
            with self.subTest(script=script):
                log = directory / 'opened.txt'
                p = isolated(directory, audit, self.root, log, script, *args)
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                self.assertEqual(set(log.read_text().splitlines()), expected)

    def test_contract_edit_matching_a_product_mutant_is_refused(self):
        root, directory = self.candidate()
        digest = hashlib.sha256((root / input_manifest.HARNESS_RECORD).read_bytes()).hexdigest()
        refusal = 'unmapped record requires context/duplicate disposition and a reason; live findings must be reconciled in STATUS before replanning'
        for name, old in (('scripts/docs-migrate.py', refusal), ('tests/fixtures/acceptance-v2/contract.json', refusal)):
            self.edited(name, lambda b: b.replace(old.encode(), b'unmapped record: carry on', 1), root)
        head = commit(root)
        path = directory / 'packet.json'
        p = invoke(root, RUNNER, '--runtime-root', root, '--result', path, '--source-commit', head,
                   '--harness-sha256', digest)
        self.assert_reject(p, 'harness files do not match tests/harness.sha256: tests/fixtures/acceptance-v2/contract.json')
        # Re-recording makes the in-tree check agree, but not the reviewer's pin or the external check.
        (root / input_manifest.HARNESS_RECORD).write_text(input_manifest.harness_record(root))
        commit(root)
        packet, hashes = generate(root, directory)
        path.write_text(json.dumps(packet))
        self.assertEqual(invoke(root, VALIDATOR, path, MANIFEST, hashes).returncode, 0,
                         'documented limit: a re-recorded tree satisfies its own check')
        self.assert_reject(invoke(root, VALIDATOR, '--harness-sha256', digest, path, MANIFEST, hashes),
                           'harness record does not match the reviewer pin')
        runner, validator = external(self.root, root, directory, '--harness-sha256', digest)
        self.assert_reject(validator, 'candidate judging files differ from the trusted checkout: '
                                      'tests/fixtures/acceptance-v2/contract.json, tests/harness.sha256')

    # R4: the external check ---------------------------------------------------------------

    def test_external_check_accepts_an_unchanged_candidate(self):
        candidate, directory = self.candidate()
        digest = hashlib.sha256((self.root / input_manifest.HARNESS_RECORD).read_bytes()).hexdigest()
        runner, validator = external(self.root, candidate, directory, '--harness-sha256', digest)
        self.assertEqual(runner.returncode, 0, runner.stderr)
        self.assertEqual((validator.returncode, json.loads(validator.stdout or '{}')),
                         (0, {'accepted': True, 'cases': 4}), validator.stderr)

    def test_external_check_rejects_a_product_mutant_by_behavior(self):
        candidate, directory = self.candidate()
        self.edited('scripts/docs-doctor.py', lambda b: b.replace(
            b'root_transition = bool(stack) and matched == 0', b'root_transition = False', 1), candidate)
        commit(candidate)
        runner, validator = external(self.root, candidate, directory)
        self.assertEqual(runner.returncode, 1, runner.stderr)
        self.assertEqual(validator.returncode, 1, validator.stdout)
        self.assertIn('REJECT', validator.stderr)
        self.assertNotIn('candidate judging files differ', validator.stderr)

    def test_external_check_never_imports_candidate_code(self):
        candidate, directory = self.candidate()
        marker = directory / 'imported'
        planted = 'open(%r, "w").write("candidate code ran")\n' % str(marker)
        for name in ('tests/acceptance_gate.py', 'tests/input_manifest.py', 'tests/acceptance_evidence.py'):
            self.edited(name, lambda b: planted.encode() + b, candidate)
        commit(candidate)
        runner, validator = external(self.root, candidate, directory)
        self.assert_reject(validator, 'candidate judging files differ from the trusted checkout: tests/acceptance_evidence.py')
        self.assertFalse(marker.exists(), 'the trusted checkout executed candidate judging code')

    def test_runtime_root_must_be_the_subject_being_judged(self):
        candidate, directory = self.candidate()
        runner, _ = external(self.root, candidate, directory)
        self.assertEqual(runner.returncode, 0, runner.stderr)
        # The candidate's packet, judged as if it described the trusted checkout.
        p = isolated(self.root, VALIDATOR, directory / 'external-result.json', MANIFEST, directory / 'external-hashes.json')
        self.assert_reject(p, 'runtime root must be the subject checkout being judged')

    # R6: the runner reports no verdict ----------------------------------------------------

    def test_runner_verifies_the_harness_and_never_reports_acceptance(self):
        root, directory = self.candidate()
        head = commit(root)
        ok = invoke(root, RUNNER, '--runtime-root', root, '--result', directory / 'r.json', '--source-commit', head)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertNotIn('accepted', ok.stdout + ok.stderr)
        self.edited('tests/acceptance_evidence.py', lambda b: b + b'\n', root)
        head = commit(root)
        p = invoke(root, RUNNER, '--runtime-root', root, '--result', directory / 'r.json', '--source-commit', head)
        self.assert_reject(p, 'harness files do not match tests/harness.sha256: tests/acceptance_evidence.py')


if __name__ == '__main__':
    unittest.main()
