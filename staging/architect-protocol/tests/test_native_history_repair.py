"""D-1 findings: original native triples and bounded committed attempt history.

Controls use real Git ancestry and public CLI calls. Synthetic role receipts
never establish an actual review. Binding twins are frozen before declaration;
history tests retain every ancestor and do not use the twin helper.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import native_fixture as n
import packet_fixture as f
import test_architect_binding as b


def execute(doctor, root):
    return subprocess.run([sys.executable, '-B', str(doctor), str(root)],
        capture_output=True, text=True, timeout=30,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))


def rewrite_receipt(root, item):
    item['record']['receipt'] = n.write(root, item['record']['receipt']['path'], item['raw'])


class NativeRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='native original subjects ')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'control'
        self.packet = n.build(self.root)
        self.check(self.root, 0)
        self.assertEqual(len(set(self.packet['subjects'].values())), 4)
        self.assertEqual(len({x['stdout_sha256'] for x in self.packet['observations']}), 4)
        for item in self.packet['completed'].values():
            ref = item['triple']['contract']
            self.assertEqual(n.sha(n.blob(self.root, item['record']['subject_commit'], ref['path'])), ref['sha256'])
        self.serial = 0

    def check(self, root, code, diagnosis=None, doctor=b.DOCTOR):
        result = execute(doctor, root)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        if diagnosis:
            self.assertIn(diagnosis, result.stdout)
        return result

    def twin(self, change):
        self.serial += 1
        root = self.base / ('twin-' + str(self.serial))
        packet = n.build(root, before_freeze=change)
        return root, packet

    def test_earlier_native_digest_claims(self):
        for attempt in ('A-1', 'G-1', 'G-2'):
            for field in ('contract_sha256', 'input_manifest_sha256', 'evidence_manifest_sha256'):
                with self.subTest(attempt=attempt, field=field):
                    def change(root, completed, subjects, contracts):
                        item = completed[attempt]
                        item['raw'][field] = '0' * 64
                        rewrite_receipt(root, item)
                    root, _ = self.twin(change)
                    self.check(root, 1, 'reviewer ' + field + ' mismatch')

    def test_old_contract_must_be_original_blob(self):
        def change(root, completed, subjects, contracts):
            item = completed['A-1']; ref = item['triple']['contract']
            changed = copy.deepcopy(contracts['A-1'][0]); changed['findings'] = ['other-finding']
            item['triple']['contract'] = n.write(root, ref['path'], changed)
            item['raw']['contract_sha256'] = item['triple']['contract']['sha256']
            rewrite_receipt(root, item)
        root, _ = self.twin(change)
        self.check(root, 1, 'native contract differs from original subject')

    def test_native_stage_belongs_to_original_contract(self):
        def change(attempt, value):
            if attempt == 'A-1': value['stages'] = ['UNDECLARED']
        root = self.base / 'wrong-original-stage'
        n.build(root, original_contract=change)
        self.check(root, 1, 'native stage absent from original contract scope')

    def test_old_input_scope_is_checked_against_own_subject(self):
        def change(root, completed, subjects, contracts):
            item = completed['A-1']; ref = item['triple']['input_manifest']
            value = json.loads((root / ref['path']).read_text())
            value['files'].pop('runtime.py')
            files = value['files']
            value['tree_sha256'] = n.sha(''.join(p+':'+files[p]['mode']+':'+files[p]['sha256']+'\n' for p in sorted(files)).encode())
            item['triple']['input_manifest'] = n.write(root, ref['path'], value)
            item['raw']['input_manifest_sha256'] = item['triple']['input_manifest']['sha256']
            rewrite_receipt(root, item)
        root, _ = self.twin(change)
        self.check(root, 1, 'input scope differs')

    def test_old_evidence_output_remains_required(self):
        def change(root, completed, subjects, contracts):
            (root / completed['G-1']['command_output']['path']).write_bytes(b'altered original output\n')
        root, _ = self.twin(change)
        self.check(root, 1, 'evidence file digest mismatch')

    def test_old_generation_rejects_unrelated_and_behavior_changed(self):
        for kind in ('unrelated', 'behavior-change'):
            with self.subTest(kind=kind):
                def change(root, completed, subjects, contracts):
                    item = completed['A-1']
                    if kind == 'unrelated':
                        generation = f.git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                            'commit-tree', f.git(root, 'rev-parse', 'HEAD^{tree}'), '-m', 'Unrelated synthetic generation')
                    else:
                        generation = subjects['G-1']
                    ref = item['triple']['evidence_manifest']
                    evidence = json.loads((root / ref['path']).read_text())
                    evidence['generation_commits'] = [generation]
                    item['triple']['evidence_manifest'] = n.write(root, ref['path'], evidence)
                    item['raw'].update(evidence_generation_commits=[generation],
                        evidence_manifest_sha256=item['triple']['evidence_manifest']['sha256'])
                    rewrite_receipt(root, item)
                root, _ = self.twin(change)
                self.check(root, 1, 'generation subject not permitted' if kind == 'unrelated'
                    else 'unreviewed reporting delta: runtime.py')

    def test_native_digest_guard_removal(self):
        def change(root, completed, subjects, contracts):
            item = completed['A-1']; item['raw']['evidence_manifest_sha256'] = '0' * 64
            rewrite_receipt(root, item)
        root, _ = self.twin(change)
        self.check(root, 1, 'reviewer evidence_manifest_sha256 mismatch')
        scripts = self.base / 'mutant-scripts'
        shutil.copytree(b.ROOT / 'scripts', scripts, ignore=shutil.ignore_patterns('__pycache__'))
        path = scripts / 'architect_packet.py'; source = path.read_text()
        guard = "need(result[field]==bindings[key]['sha256'],'reviewer '+field+' mismatch')"
        self.assertEqual(source.count(guard), 1)
        path.write_text(source.replace(guard, 'pass'))
        self.check(self.root, 0, doctor=scripts / 'architect-doctor.py')
        self.check(root, 0, doctor=scripts / 'architect-doctor.py')

    def test_nominated_f_rechecks_native_binding(self):
        state = self.packet['state']; original = copy.deepcopy(state)
        item = self.packet['completed']['A-1']; path = self.root / item['record']['receipt']['path']
        original_bytes = path.read_bytes()
        item['raw']['evidence_manifest_sha256'] = '0' * 64
        rewrite_receipt(self.root, item)
        n.write(self.root, f.PACKET + 'STATE.json', state)
        invalid_f = f.commit(self.root)
        self.check(self.root, 1, 'reviewer evidence_manifest_sha256 mismatch')
        path.write_bytes(original_bytes)
        self.packet['state'] = original
        accepted = dict(self.packet, state=original, reporting=invalid_f)
        # The current native records are restored; immutable F remains invalid.
        accept_native(self.root, accepted)
        self.check(self.root, 1, 'accepted reporting packet invalid: reviewer evidence_manifest_sha256 mismatch')


def accept_native(root, packet):
    state = packet['state']
    review = {'schema': 2, 'kind': 'architect-reporting-review', 'behavior_commit': packet['behavior'],
        'reporting_commit': packet['reporting'], 'verdict': 'PASS', 'reviewer_task': state['roles']['reviewer'],
        'handoff_sha256': state['handoff']['sha256']}
    review_ref = f.write(root, f.PACKET + 'external-review.json', review)
    response = {'schema': 2, 'kind': 'architect-acceptance', 'behavior_commit': packet['behavior'],
        'reporting_commit': packet['reporting'], 'verdict': 'PASS', 'components': {'core': 'PASS'},
        'architect_task': state['roles']['architect'], 'reporting_review_sha256': review_ref['sha256']}
    state.update(handoff_status='accepted', external_review=review_ref,
        architect_acceptance=f.write(root, f.PACKET + 'architect-response.json', response))
    f.save_state(root, state); f.commit(root)


class AttemptPreservationTests(unittest.TestCase):
    setUp = b.ArchitectBindingTests.setUp
    cli = b.ArchitectBindingTests.cli
    accepted = b.ArchitectBindingTests.accepted
    rejected = b.ArchitectBindingTests.rejected
    save = b.ArchitectBindingTests.save

    def declare(self, verdict, save=True):
        later = copy.deepcopy(self.packet['review'])
        later.update(attempt='A-2', verdict=verdict, supersedes='A-1')
        receipt = None if verdict == 'PENDING' else f.write(self.root, f.PACKET + 'attempt-2.json', later)
        self.state['stages'][0]['attempts'].append({'id': 'A-2', 'subject_commit': self.packet['behavior'],
            'verdict': verdict, 'receipt': receipt, 'supersedes': 'A-1', 'bindings': f.bindings(self.state)})
        self.state['stages'][0]['effective'] = 'A-2'
        return self.save() if save else None

    def test_committed_fail_incomplete_and_pending_cannot_disappear(self):
        for verdict in ('FAIL', 'FAIL — verification incomplete', 'PENDING'):
            with self.subTest(verdict=verdict):
                original = copy.deepcopy(self.state)
                self.declare(verdict)
                self.rejected('required stage A is not PASS')
                self.state = original; self.packet['state'] = original; self.save()
                self.rejected('attempt history preservation: declared attempt removed or reordered')
                f.write(self.root, f.PACKET + 'optional-report.md', 'Harmless later reporting\n'); f.commit(self.root)
                self.rejected('attempt history preservation: declared attempt removed or reordered')
                # Each variant has its own repository and proven passing control.
                self.setUp()

    def test_pending_can_complete_without_freezing_pending_evidence(self):
        f.fork_report(self.root, self.packet)
        complete = copy.deepcopy(self.state)
        self.state.update(stage='review', handoff=None, handoff_status=None)
        self.state['stages'][0]['attempts'][0].update(verdict='PENDING', receipt=None, bindings=None)
        self.save(); self.accepted('review')
        self.state = complete; self.packet['state'] = complete
        self.save(); self.accepted()

    def test_completed_receipt_cannot_be_replaced(self):
        self.packet['review']['reviewed_at'] = '2026-09-23T00:00:00Z'
        f.reseal_all(self.root, self.packet)
        self.rejected('attempt history preservation: completed attempt changed')

    def test_completed_result_cannot_be_replaced(self):
        # A legitimate declared failed attempt then a same-identity PASS is not repair.
        self.declare('FAIL'); self.rejected('required stage A is not PASS')
        later = copy.deepcopy(self.packet['review']); later.update(attempt='A-2', supersedes='A-1')
        ref = f.write(self.root, f.PACKET + 'attempt-2.json', later)
        self.state['stages'][0]['attempts'][-1].update(verdict='PASS', receipt=ref)
        self.packet['handoff']['review_sha256'] = ref['sha256']
        self.state['handoff'] = f.write(self.root, f.PACKET + 'HANDOFF.json', self.packet['handoff'])
        self.save(); self.rejected('attempt history preservation: completed attempt changed')

    def test_nominated_f_preserves_declared_attempts(self):
        original = copy.deepcopy(self.state)
        self.declare('FAIL'); failed = copy.deepcopy(self.state)
        self.state = original; self.packet['state'] = original
        invalid_f = self.save()
        self.rejected('attempt history preservation: declared attempt removed or reordered')
        self.packet['reporting'] = invalid_f
        f.accepted_state(self.root, self.packet)
        self.rejected('accepted reporting packet invalid: attempt history preservation: declared attempt removed or reordered')

    def test_malformed_same_contract_schema_cannot_hide_failure(self):
        for schema in (None, 999, True):
            with self.subTest(schema=schema):
                original = copy.deepcopy(self.state)
                self.declare('FAIL', save=False)
                self.state['schema'] = schema
                self.save(); self.rejected('STATE.json requires schema 2')
                self.state = original; self.packet['state'] = original; self.save()
                self.rejected('attempt history preservation: same-contract STATE requires schema 2')
                self.setUp()

    def test_malformed_pending_history_is_not_successful_history(self):
        for field, value, diagnosis in (
            ('subject_commit', 'not-a-commit', 'historical attempt subject requires full immutable subject'),
            ('receipt', 'not-a-reference', 'historical pending attempt cannot claim receipt'),
            ('bindings', False, 'historical attempt bindings fields differ'),
        ):
            with self.subTest(field=field):
                f.fork_report(self.root, self.packet)
                complete = copy.deepcopy(self.state)
                self.state.update(stage='review', handoff=None, handoff_status=None)
                attempt = self.state['stages'][0]['attempts'][0]
                attempt.update(verdict='PENDING', receipt=None, bindings=None)
                self.save(); self.accepted('review')
                attempt[field] = value; self.save()
                self.state = complete; self.packet['state'] = complete; self.save()
                self.rejected('attempt history preservation: ' + diagnosis)
                self.setUp()

    def test_reporting_merge_is_explicitly_unsupported(self):
        main = f.git(self.root, 'branch', '--show-current')
        start = f.git(self.root, 'rev-parse', 'HEAD')
        f.write(self.root, f.PACKET+'optional-report.md', 'Main reporting\n'); f.commit(self.root)
        self.accepted()
        f.git(self.root, 'checkout', '-qb', 'report-side', start)
        f.write(self.root, f.PACKET+'external-review.json', {'unused': 'reporting data'}); f.commit(self.root)
        f.git(self.root, 'checkout', '-q', main)
        f.git(self.root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
            'merge', '--no-ff', '-m', 'Synthetic reporting merge', 'report-side')
        self.rejected('attempt history: reporting merges unsupported')

    def test_state_cannot_disappear_after_declaration(self):
        original = (self.root / f.PACKET / 'STATE.json').read_bytes()
        (self.root / f.PACKET / 'STATE.json').unlink(); f.commit(self.root)
        (self.root / f.PACKET / 'STATE.json').write_bytes(original); f.commit(self.root)
        self.rejected('attempt history preservation: STATE disappeared after declaration')

    def test_committed_order_cannot_be_rewritten(self):
        self.declare('FAIL'); self.rejected('required stage A is not PASS')
        original=copy.deepcopy(self.state)
        self.state['stages'][0]['attempts'].reverse(); self.save()
        self.state=original; self.packet['state']=original
        # Repair via a new PASS keeps the legitimate prior FAIL, but cannot make
        # the intervening malformed committed ordering disappear.
        repair=copy.deepcopy(self.packet['review'])
        repair.update(attempt='A-3',supersedes='A-2')
        # A-1 retains review.json; A-3 uses another exact allowed path.
        ref=f.write(self.root,f.PACKET+'optional-report.md',repair)
        self.state['stages'][0]['attempts'].append({'id':'A-3','subject_commit':self.packet['behavior'],
            'verdict':'PASS','receipt':ref,'supersedes':'A-2','bindings':f.bindings(self.state)})
        self.state['stages'][0]['effective']='A-3'
        self.packet['handoff']['review_sha256']=ref['sha256']
        self.state['handoff']=f.write(self.root,f.PACKET+'HANDOFF.json',self.packet['handoff'])
        self.save(); self.rejected('attempt history preservation: historical supersession differs')

    def test_history_guard_removal(self):
        original = copy.deepcopy(self.state)
        self.declare('FAIL'); self.rejected('required stage A is not PASS')
        self.state = original; self.packet['state'] = original; self.save()
        self.rejected('attempt history preservation: declared attempt removed or reordered')
        scripts = Path(self.temp.name) / 'mutant-scripts'
        shutil.copytree(b.ROOT / 'scripts', scripts, ignore=shutil.ignore_patterns('__pycache__'))
        path = scripts / 'architect_packet.py'; source = path.read_text()
        guard = "need([a['id'] for a in now[:len(identifiers)]]==identifiers,'declared attempt removed or reordered: '+record['id'])"
        self.assertEqual(source.count(guard), 1)
        path.write_text(source.replace(guard, 'pass'))
        result = execute(scripts / 'architect-doctor.py', self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
