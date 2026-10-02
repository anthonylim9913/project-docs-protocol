"""Actual subprocess failures are truthful evidence, never successful outcomes.

Every synthetic receipt retains its original contract/inputs/evidence and real
outputs. One property's expected/observed mismatch is distinct from corruption.
"""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import native_fixture as n
import packet_fixture as f
import test_architect_binding as b
from test_native_history_repair import execute, accept_native, rewrite_receipt


class FailedCommandHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='truthful failed command ')
        self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.serial=0
        # A Reviewer can find a semantic defect even when all commands match.
        self.control=self.base/'semantic-control';n.build(self.control)
        self.check(self.control,0,'handoff / awaiting-architect')

    def check(self,root,code,diagnosis,doctor=b.DOCTOR):
        result=execute(doctor,root)
        self.assertEqual(result.returncode,code,result.stdout+result.stderr)
        self.assertIn(diagnosis,result.stdout);self.assertNotIn('Traceback',result.stdout+result.stderr)
        return result

    def build(self,change=None,**kwargs):
        self.serial+=1;root=self.base/str(self.serial)
        packet=n.build(root,before_freeze=change,**kwargs)
        return root,packet

    def actual_failure(self,change=None):
        return self.build(change,runtime_exits={'G-2':1})

    def test_honest_repair_and_final_preserve_real_failed_observation(self):
        saved={}
        def observe(root,completed,subjects,contracts):
            self.check(root,0,'repair; current work is not accepted')
            item=completed['G-2'];expected=contracts['G-2'][0]['evidence_checks'][0]['exit']
            evidence=json.loads((root/item['triple']['evidence_manifest']['path']).read_text())
            self.assertEqual(expected,0);self.assertEqual(evidence['commands'][0]['exit'],1)
            refs=list(item['triple'].values())+[item['record']['receipt'],item['command_output']]
            saved.update({ref['path']:(root/ref['path']).read_bytes() for ref in refs})
        root,packet=self.actual_failure(observe)
        self.check(root,0,'handoff / awaiting-architect')
        for path,content in saved.items():self.assertEqual((root/path).read_bytes(),content)
        self.assertEqual([r['exit'] for r in packet['observations']],[0,0,1,0])

    def test_accepted_chain_preserves_failed_command_history(self):
        root,packet=self.actual_failure();self.check(root,0,'handoff / awaiting-architect')
        before={ref['path']:(root/ref['path']).read_bytes() for ref in packet['completed']['G-2']['triple'].values()}
        accept_native(root,packet);self.check(root,0,'handoff / accepted')
        for path,content in before.items():self.assertEqual((root/path).read_bytes(),content)

    def test_verification_incomplete_receipt_with_complete_observations(self):
        def change(root,completed,subjects,contracts):
            item=completed['G-2']
            item['raw']['verdict']=item['record']['verdict']='FAIL — verification incomplete'
            rewrite_receipt(root,item)
        root,_=self.actual_failure(change);self.check(root,0,'handoff / awaiting-architect')

    def test_earlier_pass_still_requires_expected_outcome(self):
        root,_=self.build(runtime_exits={'G-1':1})
        self.check(root,1,'evidence command exit mismatch')

    def test_nonzero_expected_outcome_can_pass(self):
        def expected(attempt,contract):
            if attempt=='G-1':contract['evidence_checks'][0]['exit']=1
        root,_=self.build(runtime_exits={'G-1':1},original_contract=expected)
        self.check(root,0,'handoff / awaiting-architect')
        wrong,_=self.build(original_contract=expected)
        self.check(wrong,1,'evidence command exit mismatch')

    def test_latest_failed_receipt_still_blocks_handoff(self):
        root,packet=self.actual_failure();self.check(root,0,'handoff / awaiting-architect')
        f.fork_report(root,packet)
        item=packet['completed']['G-3'];item['record']['verdict']=item['raw']['verdict']='FAIL'
        rewrite_receipt(root,item)
        state=packet['state'];handoff=json.loads((root/state['handoff']['path']).read_text())
        handoff['review_sha256']=item['record']['receipt']['sha256']
        state['handoff']=n.write(root,state['handoff']['path'],handoff)
        f.save_state(root,state);f.commit(root)
        self.check(root,1,'required stage G is not PASS')

    def test_failed_observation_integrity_is_never_optional(self):
        good,_=self.actual_failure();self.check(good,0,'handoff / awaiting-architect')
        for kind,diagnosis in (
            ('altered-output','evidence file digest mismatch'),
            ('missing-output','stdout.txt missing'),
            ('input-binding','reviewer input_manifest_sha256 mismatch'),
            ('contract-binding','reviewer contract_sha256 mismatch'),
            ('missing-command','evidence command scope differs'),
            ('boolean-exit','evidence command exit must be integer'),
            ('unrelated-generation','generation subject not permitted'),
            ('changed-behavior-generation','unreviewed reporting delta: runtime.py'),
        ):
            with self.subTest(kind=kind):
                def change(root,completed,subjects,contracts):
                    item=completed['G-2']
                    if kind=='altered-output':(root/item['command_output']['path']).write_bytes(b'corrupt\n')
                    elif kind=='missing-output':(root/item['command_output']['path']).unlink()
                    elif kind.endswith('-binding'):
                        item['raw']['input_manifest_sha256' if kind=='input-binding' else 'contract_sha256']='0'*64
                        rewrite_receipt(root,item)
                    else:
                        ref=item['triple']['evidence_manifest'];evidence=json.loads((root/ref['path']).read_text())
                        if kind=='missing-command':evidence['commands']=[]
                        elif kind=='boolean-exit':evidence['commands'][0]['exit']=True
                        else:
                            if kind=='unrelated-generation':
                                revision=f.git(root,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                                    'commit-tree',f.git(root,'rev-parse','HEAD^{tree}'),'-m','Unrelated generation')
                            else:
                                # A real descendant changes behavior before being nominated.
                                (root/'runtime.py').write_text('print("unreviewed generation")\n')
                                revision=f.commit(root)
                                (root/'runtime.py').write_bytes(n.blob(root,subjects['G-2'],'runtime.py'))
                            evidence['generation_commits']=[revision]
                            item['raw']['evidence_generation_commits']=[revision]
                        item['triple']['evidence_manifest']=n.write(root,ref['path'],evidence)
                        item['raw']['evidence_manifest_sha256']=item['triple']['evidence_manifest']['sha256']
                        rewrite_receipt(root,item)
                root,_=self.actual_failure(change);self.check(root,1,diagnosis)

    def test_pass_requirement_guard_removal(self):
        root,_=self.build(runtime_exits={'G-1':1})
        self.check(root,1,'evidence command exit mismatch')
        scripts=self.base/'mutant';shutil.copytree(b.ROOT/'scripts',scripts,ignore=shutil.ignore_patterns('__pycache__'))
        path=scripts/'architect_packet.py';source=path.read_text()
        guard="require_expected=result['verdict']=='PASS'"
        self.assertEqual(source.count(guard),1)
        path.write_text(source.replace(guard,'require_expected=False'))
        self.check(self.control,0,'handoff / awaiting-architect',scripts/'architect-doctor.py')
        self.check(root,0,'handoff / awaiting-architect',scripts/'architect-doctor.py')

    def test_behavior_snapshot_guard_isolated_from_later_declarations(self):
        # Close the Reviewer's inconclusive B-only mutant with a direct B child.
        # Preserve the passing F on its original branch; create a disposable twin.
        root,packet=self.build();self.check(root,0,'handoff / awaiting-architect')
        behavior,reporting=packet['behavior'],packet['reporting']
        contract=packet['contracts']['G-3'][0]
        retained={p:n.blob(root,reporting,p) for p in contract['reporting_paths']
                  if p in n.entries(root,reporting)}
        f.git(root,'checkout','-qb','only-b-declares-failure',behavior)
        for path,data in retained.items():n.write(root,path,data)
        state=packet['state'];stage=state['stages'][1]
        stage['attempts'].pop(1)  # Omit G-2 and reconnect its successor honestly.
        item=packet['completed']['G-3']
        item['record']['supersedes']=item['raw']['supersedes']='G-1'
        rewrite_receipt(root,item)
        handoff=json.loads((root/state['handoff']['path']).read_text())
        handoff['review_sha256']=item['record']['receipt']['sha256']
        state['handoff']=n.write(root,state['handoff']['path'],handoff)
        f.save_state(root,state);bad=f.commit(root)
        self.assertEqual(f.git(root,'rev-list',behavior+'..HEAD').splitlines(),[bad])
        self.check(root,1,'attempt history preservation: declared attempt removed or reordered')
        scripts=self.base/'b-only-mutant';shutil.copytree(b.ROOT/'scripts',scripts,ignore=shutil.ignore_patterns('__pycache__'))
        path=scripts/'architect_packet.py';source=path.read_text()
        guard='for revision in [subject]+revisions:'
        self.assertEqual(source.count(guard),1)
        path.write_text(source.replace(guard,'for revision in revisions:'))
        self.check(self.control,0,'handoff / awaiting-architect',scripts/'architect-doctor.py')
        self.check(root,0,'handoff / awaiting-architect',scripts/'architect-doctor.py')


if __name__=='__main__':unittest.main()
