"""Public CLI lifecycle and exact binding controls built from valid Git packets."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import packet_fixture as f

ROOT=Path(__file__).parents[1]
DOCTOR=ROOT/'scripts/architect-doctor.py'


class ArchitectBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='architect packet ')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'project with spaces'
        self.packet=f.create(self.root)
        self.state=self.packet['state']
        self.accepted()

    def cli(self,*args):
        return subprocess.run([sys.executable,'-B',str(DOCTOR),str(self.root),*args],
            capture_output=True,text=True,timeout=15)

    def accepted(self,stage='handoff',*args):
        result=self.cli(*args);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn(stage,result.stdout);return result

    def rejected(self,diagnostic):
        result=self.cli();self.assertEqual(result.returncode,1,result.stdout+result.stderr)
        self.assertIn(diagnostic,result.stdout+result.stderr)
        self.assertNotIn('Traceback',result.stdout+result.stderr);return result

    def save(self):
        f.save_state(self.root,self.state);return f.commit(self.root)

    def alter_review(self,key,value):
        self.packet['review'][key]=value
        f.write(self.root,f.PACKET+'review.json',self.packet['review'])
        f.reseal(self.root,self.packet,'review.json')

    def test_subject_mismatch_rejects_itself(self):
        self.alter_review('subject_commit',self.packet['reporting'])
        self.rejected('reviewer subject mismatch')

    def test_descriptive_subject_cannot_downgrade_final(self):
        self.state['subject_commit']='release candidate';self.save()
        self.rejected('immutable subject')

    def test_schema_downgrade(self):
        self.state['schema']=1;self.save();self.rejected('schema 2')

    def test_missing_handoff(self):
        (self.root/f.PACKET/'HANDOFF.json').unlink();f.commit(self.root)
        self.rejected('HANDOFF.json missing')

    def test_contract_digest(self):
        self.state['contract']['sha256']='0'*64;self.save();self.rejected('contract digest mismatch')

    def test_manifest_digest(self):
        self.state['input_manifest']['sha256']='0'*64;self.save();self.rejected('input manifest digest mismatch')

    def test_input_scope_omission(self):
        manifest=self.packet['inputs'];manifest['files'].pop('runtime.py')
        manifest['tree_sha256']=f.digest(''.join(k+':'+manifest['files'][k]['mode']+':'+manifest['files'][k]['sha256']+'\n' for k in sorted(manifest['files'])).encode())
        self.state['input_manifest']=f.write(self.root,f.PACKET+'inputs.json',manifest);self.save()
        self.rejected('input scope differs')

    def test_aggregate_digest(self):
        self.packet['inputs']['tree_sha256']='0'*64
        self.state['input_manifest']=f.write(self.root,f.PACKET+'inputs.json',self.packet['inputs']);self.save()
        self.rejected('input tree digest mismatch')

    def test_dirty_input_with_index_flag(self):
        f.git(self.root,'update-index','--assume-unchanged','runtime.py')
        (self.root/'runtime.py').write_text('changed despite flag\n')
        self.rejected('working input differs: runtime.py')

    def test_committed_behavior_descendant(self):
        (self.root/'runtime.py').write_text('unreviewed\n');f.commit(self.root)
        self.rejected('unreviewed reporting delta: runtime.py')

    def test_new_test_fixture_is_behavior(self):
        f.write(self.root,'tests/new.json',{});f.commit(self.root)
        self.rejected('unreviewed reporting delta: tests/new.json')

    def test_deleted_behavior_input(self):
        (self.root/'runtime.py').unlink();f.commit(self.root)
        self.rejected('unreviewed reporting delta: runtime.py')

    def test_reporting_prefix_does_not_allow_child(self):
        f.write(self.root,f.PACKET+'optional-report.md.extra','extra\n');f.commit(self.root)
        self.rejected('unreviewed reporting delta: docs/architect/optional-report.md.extra')

    def test_exact_optional_reporting_addition(self):
        f.write(self.root,f.PACKET+'optional-report.md','Allowed report\n');f.commit(self.root)
        self.accepted()

    def test_ignored_untracked_file(self):
        (self.root/'junk.pyc').write_bytes(b'cache')
        self.rejected('untracked path: junk.pyc')

    def test_ignored_directory(self):
        (self.root/'cache').mkdir();(self.root/'cache/value').write_text('cache')
        self.rejected('untracked path: cache/')

    def test_dirty_report(self):
        (self.root/f.PACKET/'command.txt').write_text('changed\n')
        self.rejected('working tracked file differs: docs/architect/command.txt')

    def test_unresolved_generation(self):
        self.packet['evidence']['generation_commits']=['a'*40]
        self.state['evidence_manifest']=f.write(self.root,f.PACKET+'evidence.json',self.packet['evidence']);self.save()
        self.rejected('generation commit unresolved')

    def test_evidence_output_digest(self):
        f.write(self.root,f.PACKET+'command.txt','substituted output\n');f.commit(self.root)
        self.rejected('evidence file digest mismatch')

    def test_evidence_command_exit(self):
        self.packet['evidence']['commands'][0]['exit']=99
        self.state['evidence_manifest']=f.write(self.root,f.PACKET+'evidence.json',self.packet['evidence']);self.save()
        self.rejected('evidence command exit mismatch')

    def test_stage_fail_cannot_be_final(self):
        self.alter_review('verdict','FAIL')
        self.state['stages'][0]['attempts'][0]['verdict']='FAIL';self.save()
        self.rejected('required stage A is not PASS')

    def test_omitted_stage(self):
        self.state['stages']=[];self.save();self.rejected('stage scope differs')

    def test_duplicate_stage(self):
        self.state['stages'].append(copy.deepcopy(self.state['stages'][0]));self.save()
        self.rejected('stage scope differs')

    def test_live_findings_are_scoped(self):
        # Unrelated project ledger content is outside release finding closure.
        self.state['open_findings']=['R1'];self.save();self.rejected('in-scope findings remain open')

    def test_artifact_parent_symlink(self):
        directory=self.root/f.PACKET;outside=Path(self.temp.name)/'moved packet'
        directory.rename(outside);directory.symlink_to(outside,target_is_directory=True)
        self.rejected('symlinked artifact')

    def test_artifact_fifo(self):
        path=self.root/f.PACKET/'inputs.json';path.unlink();os.mkfifo(path)
        self.rejected('artifact must be regular')

    def test_duplicate_json_key(self):
        path=self.root/f.PACKET/'STATE.json';text=path.read_text();path.write_text(text.replace('"schema": 2','"schema": 2, "schema": 2'))
        f.commit(self.root);self.rejected('duplicate JSON key')

    def test_boolean_schema_is_not_integer(self):
        self.state['schema']=True;self.save();self.rejected('schema 2')

    def test_pending_review_is_honest(self):
        f.fork_report(self.root,self.packet)
        self.state.update(stage='review',handoff=None,handoff_status=None)
        attempt=self.state['stages'][0]['attempts'][0];attempt.update(verdict='PENDING',receipt=None)
        self.save();self.accepted('review')

    def test_implement_allows_unreviewed_work(self):
        self.state.update(stage='implement',input_manifest=None,evidence_manifest=None,handoff=None,handoff_status=None)
        self.state['stages'][0]['attempts'][0].update(verdict='PENDING',receipt=None)
        self.save();(self.root/'runtime.py').write_text('work in progress\n')
        self.accepted('implement')

    def test_repair_preserves_failure(self):
        self.alter_review('verdict','FAIL')
        self.state.update(stage='repair',handoff=None,handoff_status=None)
        self.state['stages'][0]['attempts'][0]['verdict']='FAIL';self.save()
        self.accepted('repair')

    def test_accepted_requires_actual_response(self):
        self.state['handoff_status']='accepted';self.save()
        self.rejected('accepted state requires Architect response')

    def test_production_rejects_example_mode(self):
        self.state['mode']='structural-example';self.save()
        self.rejected('explicit --structural-example')


if __name__=='__main__':unittest.main()
