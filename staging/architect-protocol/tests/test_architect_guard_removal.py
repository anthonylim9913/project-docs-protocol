"""Intact and guard-removed public CLIs; synthetic fixtures never assert real review."""
import copy
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import packet_fixture as f
import test_architect_binding as binding


class GuardRemovalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='architect guard ');self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.root=self.base/'project'
        self.packet=f.create(self.root);self.state=self.packet['state']
        self.scripts=self.base/'scripts';shutil.copytree(binding.ROOT/'scripts',self.scripts,
            ignore=shutil.ignore_patterns('__pycache__'))
        self.source=self.scripts/'architect_packet.py'
        self.doctor=self.scripts/'architect-doctor.py'
        self.run_cli(0)

    def run_cli(self,exit_code,diagnosis=None):
        result=subprocess.run([sys.executable,'-B',str(self.doctor),str(self.root)],
            capture_output=True,text=True,timeout=20,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(result.returncode,exit_code,result.stdout+result.stderr)
        self.assertNotIn('Traceback',result.stderr)
        if diagnosis:self.assertIn(diagnosis,result.stdout)
        return result

    def remove(self,old,new='pass',count=1):
        source=self.source.read_text();self.assertEqual(source.count(old),count,'mutant anchor changed')
        self.source.write_text(source.replace(old,new))

    def save(self):f.save_state(self.root,self.state);f.commit(self.root)

    def test_reviewer_subject_guard(self):
        f.fork_report(self.root,self.packet)
        self.packet['review']['subject_commit']=self.packet['reporting'];f.reseal_all(self.root,self.packet)
        self.run_cli(1,'reviewer subject mismatch')
        self.remove("need(result['subject_commit']==attempt['subject_commit'],'reviewer subject mismatch')")
        self.remove("need(result['subject_commit']==state['subject_commit'],'reviewer subject mismatch')")
        self.run_cli(0)

    def test_final_verdict_guard(self):
        f.fork_report(self.root,self.packet)
        self.packet['review']['verdict']='FAIL';self.state['stages'][0]['attempts'][0]['verdict']='FAIL'
        f.reseal_all(self.root,self.packet);self.run_cli(1,'required stage A is not PASS')
        self.remove("need(last['verdict']=='PASS','required stage '+record['id']+' is not PASS')")
        self.run_cli(0)

    def test_input_scope_guard(self):
        f.fork_report(self.root,self.packet)
        self.packet['inputs']['files'].pop('runtime.py')
        files=self.packet['inputs']['files'];self.packet['inputs']['tree_sha256']=f.digest(
            ''.join(p+':'+files[p]['mode']+':'+files[p]['sha256']+'\n' for p in sorted(files)).encode())
        f.reseal_all(self.root,self.packet);self.run_cli(1,'input scope differs')
        self.remove("need(isinstance(files,dict) and set(files)==expected,'input scope differs')",'expected=set(files)')
        self.run_cli(0)

    def test_contract_hash_guard(self):
        f.fork_report(self.root,self.packet)
        self.state['contract']['sha256']='0'*64;f.reseal_all(self.root,self.packet)
        self.run_cli(1,'contract digest mismatch')
        self.remove("need(digest(data)==ref['sha256'],label+' digest mismatch')")
        self.run_cli(0)

    def test_aggregate_guard(self):
        f.fork_report(self.root,self.packet)
        self.packet['inputs']['tree_sha256']='0'*64;f.reseal_all(self.root,self.packet)
        self.run_cli(1,'input tree digest mismatch')
        self.remove("need(manifest['tree_sha256']==digest(''.join(rows).encode()),'input tree digest mismatch')")
        self.run_cli(0)

    def test_effective_pointer_guard(self):
        # Wrong pointer to a missing attempt is one changed property. The separate
        # earlier-PASS/later-FAIL regression covers the composite final verdict.
        self.state['stages'][0]['effective']='missing-attempt';self.save()
        self.run_cli(1,'effective attempt must be final attempt')
        self.remove("need(record['effective']==ids[-1],'effective attempt must be final attempt')")
        self.run_cli(0)

    def test_pending_subject_guard(self):
        f.fork_report(self.root,self.packet)
        self.state.update(stage='review',handoff=None,handoff_status=None)
        attempt=self.state['stages'][0]['attempts'][0];attempt.update(verdict='PENDING',receipt=None)
        self.save();self.run_cli(0,'review')
        attempt['subject_commit']=self.packet['reporting'];self.save()
        self.run_cli(1,'active attempt subject mismatch')
        self.remove("need(last['subject_commit']==state['subject_commit'],'active attempt subject mismatch')")
        self.run_cli(0)

    def test_accepted_immutable_evidence_guard(self):
        output=self.root/f.PACKET/'command.txt';original=output.read_bytes()
        output.write_text('corrupted only in F\n');bad=f.commit(self.root)
        output.write_bytes(original);f.accepted_state(self.root,self.packet);self.run_cli(0,'accepted')
        self.packet['reporting']=bad;f.accepted_state(self.root,self.packet)
        self.run_cli(1,'accepted reporting packet invalid: evidence file digest mismatch')
        self.remove("validate_project(CommittedProject(project,reporting),state['_state_path'].rsplit('/',1)[0])")
        self.run_cli(0,'accepted')

    def test_original_historical_manifest_guard(self):
        from test_architect_history import historical
        other=self.base/'history'
        f.create(other,historical=historical('legacy-c'));self.root=other;self.run_cli(0)
        def substitute(root,raw,imported):
            imported['bindings']['input_manifest']=f.write(root,'history/inputs.json',{'substituted':'scope'})
        self.root=self.base/'substitution'
        f.create(self.root,historical=historical('legacy-c',substitute))
        self.run_cli(1,'original historical input_manifest digest mismatch')
        self.remove("need(ref['sha256']==value,'original historical '+key+' digest mismatch')")
        self.run_cli(0)


if __name__=='__main__':unittest.main()
