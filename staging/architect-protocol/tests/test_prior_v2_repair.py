"""Original supported v2 PASS/FAIL/PASS bytes survive frozen historical import."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import packet_fixture as f
import test_architect_binding as b
from test_native_history_repair import execute


def original_chain(root):
    packet = f.create(root)
    # Establish a distinct native path before its first declaration; never edit
    # the identity of a completed receipt in the selected history afterwards.
    f.fork_report(root, packet)
    state = packet['state']; first = state['stages'][0]['attempts'][0]
    first['receipt'] = f.write(root, f.PACKET+'attempt-1.json', packet['review'])
    packet['handoff']['review_sha256'] = first['receipt']['sha256']
    state['handoff'] = f.write(root, f.PACKET+'HANDOFF.json', packet['handoff'])
    f.save_state(root, state); f.commit(root)
    raw = copy.deepcopy(packet['review']); raw.update(attempt='A-2', verdict='FAIL', supersedes='A-1')
    second = {'id':'A-2','subject_commit':packet['behavior'],'verdict':'FAIL','supersedes':'A-1',
        'receipt':f.write(root, f.PACKET+'attempt-2.json',raw),'bindings':f.bindings(state)}
    state['stages'][0].update(effective='A-2', attempts=[first,second])
    state.update(stage='repair',handoff=None,handoff_status=None)
    f.save_state(root,state);f.commit(root)
    packet['review'].update(attempt='A-3',supersedes='A-2')
    last = {'id':'A-3','subject_commit':packet['behavior'],'verdict':'PASS','supersedes':'A-2',
        'receipt':f.write(root,f.PACKET+'review.json',packet['review']),'bindings':f.bindings(state)}
    packet['handoff']['review_sha256']=last['receipt']['sha256']
    state.update(stage='handoff',handoff_status='awaiting-architect',
        handoff=f.write(root,f.PACKET+'HANDOFF.json',packet['handoff']))
    state['stages'][0].update(effective='A-3',attempts=[first,second,last])
    f.save_state(root,state);packet['reporting']=f.commit(root)
    return packet


def import_chain(root, packet, change=None):
    state=packet['state'];old=copy.deepcopy(packet)
    refs={key:f.write(root,f.PACKET+'historical-'+key+'.json',old[value]) for key,value in
        [('contract','contract'),('input_manifest','inputs'),('evidence_manifest','evidence')]}
    receipt=f.write(root,f.PACKET+'historical-review.json',old['review'])
    prior=[copy.deepcopy(a['receipt']) for a in state['stages'][0]['attempts'][:-1]]
    if change:
        raw=json.loads((root/prior[1]['path']).read_text());change(raw)
        prior[1]=f.write(root,prior[1]['path'],raw)
    imported={'shape':'v2','receipt':receipt,'subject_commit':old['behavior'],'baseline_commit':None,
        'bindings':refs,'prior_receipts':prior}
    packet['contract'].update(stages=['A','B'],historical_stages={'A':imported})
    packet['contract']['reporting_paths'] += [ref['path'] for ref in refs.values()]+[receipt['path']]
    state['stages']=[{'id':'A','effective':'A-3','attempts':[{'id':'A-3','subject_commit':old['behavior'],
        'verdict':'PASS','receipt':receipt,'supersedes':None,'bindings':None}]},{}]
    f.refreeze(root,packet)
    return prior


class PriorV2RepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='original v2 chain ');self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'project'
        self.packet=original_chain(self.root)
        self.check(0)
        control=self.base/'import-control';shutil.copytree(self.root,control)
        import_chain(control,copy.deepcopy(self.packet))
        result=execute(b.DOCTOR,control)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.originals={a['receipt']['path']:(self.root/a['receipt']['path']).read_bytes()
            for a in self.packet['state']['stages'][0]['attempts']}

    def check(self,code,diagnosis=None,doctor=b.DOCTOR):
        result=execute(doctor,self.root)
        self.assertEqual(result.returncode,code,result.stdout+result.stderr)
        self.assertNotIn('Traceback',result.stdout+result.stderr)
        if diagnosis:self.assertIn(diagnosis,result.stdout)

    def test_unmodified_pass_fail_repair_pass_import(self):
        prior=import_chain(self.root,self.packet);self.check(0)
        for ref in prior:self.assertEqual((self.root/ref['path']).read_bytes(),self.originals[ref['path']])
        self.assertEqual((self.root/f.PACKET/'historical-review.json').read_bytes(),self.originals[f.PACKET+'review.json'])

    def test_prior_required_fields_keep_original_types(self):
        cases=[('subject_commit',7,'prior v2 receipt subject requires full immutable subject'),
            ('reviewer_task',[],'prior v2 receipt reviewer task mismatch'),
            ('contract_sha256','not-a-digest','prior v2 receipt contract_sha256 must be lowercase SHA256'),
            ('input_manifest_sha256',False,'prior v2 receipt input_manifest_sha256 must be lowercase SHA256'),
            ('evidence_manifest_sha256',[],'prior v2 receipt evidence_manifest_sha256 must be lowercase SHA256'),
            ('reviewed_at',None,'prior v2 receipt reviewed_at must be a nonempty string'),
            ('extra',True,'prior v2 receipt fields differ')]
        for field,value,diagnosis in cases:
            with self.subTest(field=field):
                self.setUp()
                import_chain(self.root,self.packet,lambda raw:raw.__setitem__(field,value))
                self.check(1,diagnosis)

    def test_prior_shape_guard_removal(self):
        import_chain(self.root,self.packet,lambda raw:raw.__setitem__('contract_sha256','not-a-digest'))
        self.check(1,'prior v2 receipt contract_sha256 must be lowercase SHA256')
        scripts=self.base/'mutant-scripts';shutil.copytree(b.ROOT/'scripts',scripts,ignore=shutil.ignore_patterns('__pycache__'))
        path=scripts/'architect_packet.py';source=path.read_text()
        guard="review_shape(project,prior,state,'prior v2 receipt')"
        self.assertEqual(source.count(guard),1);path.write_text(source.replace(guard,'pass'))
        self.check(0,doctor=scripts/'architect-doctor.py')


if __name__=='__main__':unittest.main()
