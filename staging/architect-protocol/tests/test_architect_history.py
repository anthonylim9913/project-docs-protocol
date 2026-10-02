"""Historical formats retain original bytes, scope and original hash obligations."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import packet_fixture as f
import test_architect_binding as binding


def historical(shape, change=None, contract_digest=False):
    def prepare(root, contract, roles):
        baseline=f.commit(root)
        manifest=f.write(root,'history/inputs.json',{'original_scope':['runtime.py'],'subject':baseline})
        packet_commit=f.commit(root)
        raw={'stage':'A','verdict':'PASS','reviewer_task':roles['reviewer']}
        if shape=='legacy-a':
            raw.update(schema=1,kind='independent-stage-review',packet_commit=packet_commit,
                baseline_behavior_commit=baseline,baseline_input_manifest=manifest)
        elif shape=='legacy-b':
            raw.update(schema=1,kind='independent-stage-review',subject_commit=packet_commit,input_manifest=manifest)
        else:
            raw.update(subject_commit=packet_commit,submitted_manifest_sha256=manifest['sha256'])
        bindings={'input_manifest':manifest}
        if contract_digest:
            original=f.write(root,'history/original-contract.json',{'original':'scope'})
            bindings['contract']=original;raw['acceptance_contract_hash']=original['sha256']
        receipt=f.write(root,'history/review.json',raw)
        imported={'shape':shape,'receipt':receipt,'subject_commit':packet_commit,
            'baseline_commit':baseline if shape=='legacy-a' else None,'bindings':bindings,'prior_receipts':[]}
        if change:change(root,raw,imported)
        contract.update(stages=['A','G'],historical_stages={'A':imported})
    return prepare


class HistoricalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='architect historical ');self.addCleanup(self.temp.cleanup)
        self.serial=0

    def run_fixture(self,shape,change=None,contract_digest=False):
        self.serial+=1;root=Path(self.temp.name)/str(self.serial)
        packet=f.create(root,historical=historical(shape,change,contract_digest))
        result=subprocess.run([sys.executable,'-B',str(binding.DOCTOR),str(root)],capture_output=True,text=True,timeout=15)
        self.assertNotIn('Traceback',result.stdout+result.stderr)
        return root,packet,result

    def passing(self,shape,**kwargs):
        root,packet,result=self.run_fixture(shape,**kwargs)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        return root,packet

    def check_changed(self,shape,change,diagnosis,**kwargs):
        self.passing(shape,**kwargs)
        _,_,result=self.run_fixture(shape,change,**kwargs)
        self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn(diagnosis,result.stdout)

    def test_all_real_legacy_shapes_pass_without_invented_contract_digest(self):
        for shape in ('legacy-a','legacy-b','legacy-c'):
            with self.subTest(shape=shape):self.passing(shape)

    def test_relocated_original_manifest_passes(self):
        def move(root,raw,imported):
            original=(root/imported['bindings']['input_manifest']['path']).read_text()
            imported['bindings']['input_manifest']=f.write(root,'relocated/historical-inputs.json',original)
        for shape in ('legacy-a','legacy-b','legacy-c'):
            with self.subTest(shape=shape):self.passing(shape,change=move)

    def test_paired_wrapper_and_manifest_substitution_reaches_original_digest(self):
        def substitute(root,raw,imported):
            imported['bindings']['input_manifest']=f.write(root,'history/inputs.json',{'substituted':'scope'})
        for shape in ('legacy-a','legacy-b','legacy-c'):
            with self.subTest(shape=shape):
                self.check_changed(shape,substitute,'original historical input_manifest digest mismatch')

    def test_present_original_contract_digest_is_mandatory(self):
        def substitute(root,raw,imported):
            imported['bindings']['contract']=f.write(root,'history/original-contract.json',{'substituted':'contract'})
        self.check_changed('legacy-b',substitute,'original historical contract digest mismatch',contract_digest=True)

    def test_original_digest_cannot_be_removed(self):
        def remove(root,raw,imported):
            raw.pop('submitted_manifest_sha256');imported['receipt']=f.write(root,'history/review.json',raw)
        self.check_changed('legacy-c',remove,'original historical input_manifest must be lowercase SHA256')

    def test_a_packet_and_baseline_identities_remain_distinct(self):
        def mismatch(root,raw,imported):imported['baseline_commit']=imported['subject_commit']
        self.check_changed('legacy-a',mismatch,'historical baseline mismatch')

    def test_known_shape_prevents_downgrade(self):
        def wrong(root,raw,imported):
            raw['schema']=2;imported['receipt']=f.write(root,'history/review.json',raw)
        self.check_changed('legacy-b',wrong,'historical legacy schema/kind mismatch')

    def test_c_cannot_invent_schema_fields(self):
        def wrong(root,raw,imported):
            raw['schema']=1;imported['receipt']=f.write(root,'history/review.json',raw)
        self.check_changed('legacy-c',wrong,'historical legacy-c shape mismatch')

    def test_frozen_selection_cannot_be_changed_by_state(self):
        root,packet=self.passing('legacy-c')
        packet['state']['stages'][0]['attempts'][0]['receipt']=packet['state']['stages'][-1]['attempts'][0]['receipt']
        f.save_state(root,packet['state']);f.commit(root)
        result=subprocess.run([sys.executable,'-B',str(binding.DOCTOR),str(root)],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,1,result.stdout);self.assertIn('frozen historical receipt selection changed',result.stdout)

    def test_import_cannot_cover_final_gate(self):
        def change(root,raw,imported):pass
        root,packet=self.passing('legacy-c')
        contract=packet['contract'];contract['historical_stages']['G']=copy.deepcopy(contract['historical_stages']['A'])
        packet['state']['contract']=f.write(root,f.PACKET+'contract.json',contract)
        f.save_state(root,packet['state']);f.commit(root)
        result=subprocess.run([sys.executable,'-B',str(binding.DOCTOR),str(root)],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,1,result.stdout);self.assertIn('final stage cannot use historical compatibility',result.stdout)

    def test_v2_original_fields_are_not_downgraded(self):
        for field,value,diagnosis in (
            ('evidence_generation_commits',['a'*40],'generation commit unresolved'),
            ('attempt','WRONG','historical attempt mismatch'),
            ('reviewed_at',None,'historical v2 receipt reviewed_at must be a nonempty string'),
            ('supersedes','missing-attempt','historical supersession mismatch'),
        ):
            with self.subTest(field=field):
                self.serial+=1;root=Path(self.temp.name)/str(self.serial)
                packet,raw=f.history(root)
                def run():
                    return subprocess.run([sys.executable,'-B',str(binding.DOCTOR),str(root)],
                        capture_output=True,text=True,timeout=15)
                control=run();self.assertEqual(control.returncode,0,control.stdout+control.stderr)
                raw[field]=value
                ref=f.write(root,f.PACKET+'historical-review.json',raw)
                packet['contract']['historical_stages']['A']['receipt']=ref
                packet['state']['stages'][0]['attempts'][0]['receipt']=ref
                f.refreeze(root,packet)
                result=run();self.assertEqual(result.returncode,1,result.stdout+result.stderr)
                self.assertIn(diagnosis,result.stdout);self.assertNotIn('Traceback',result.stderr)


if __name__=='__main__':unittest.main()
