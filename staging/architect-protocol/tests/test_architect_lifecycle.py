"""Bounded lifecycle/external acceptance cases; synthetic approval is labeled."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import packet_fixture as f
import test_architect_binding as binding


class LifecycleTests(unittest.TestCase):
    setUp=binding.ArchitectBindingTests.setUp
    cli=binding.ArchitectBindingTests.cli
    accepted=binding.ArchitectBindingTests.accepted
    rejected=binding.ArchitectBindingTests.rejected
    save=binding.ArchitectBindingTests.save
    alter_review=binding.ArchitectBindingTests.alter_review

    def test_scope_without_invented_commit(self):
        self.state=f.scope_state();self.save();self.accepted('scope')

    def test_baseline_before_final_reviews(self):
        self.state.update(stage='baseline',input_manifest=None,evidence_manifest=None,handoff=None,handoff_status=None)
        self.state['stages'][0]['attempts'][0].update(verdict='PENDING',receipt=None)
        self.save();self.accepted('baseline')

    def test_example_requires_explicit_opt_in_and_cannot_be_final(self):
        self.state=f.scope_state(True);self.save()
        self.rejected('explicit --structural-example')
        result=self.accepted('STRUCTURAL','--structural-example')
        self.assertNotIn('PASS architect',result.stdout)
        self.state['stage']='handoff';self.save()
        changed=self.cli('--structural-example')
        self.assertEqual(changed.returncode,1);self.assertIn('unfrozen scope',changed.stdout)

    def test_accepted_prior_pair_with_later_reporting_head(self):
        f.accepted_state(self.root,self.packet);self.accepted('accepted')
        f.write(self.root,f.PACKET+'optional-report.md','Further narrative\n');f.commit(self.root)
        self.accepted('accepted')

    def test_accepted_wrong_reporting_pair(self):
        _,response=f.accepted_state(self.root,self.packet);self.accepted('accepted')
        response['reporting_commit']=self.packet['behavior']
        self.state['architect_acceptance']=f.write(self.root,f.PACKET+'architect-response.json',response);self.save()
        self.rejected('accepted reporting subject mismatch')

    def test_accepted_matching_but_nonhandoff_ancestor(self):
        review,response=f.accepted_state(self.root,self.packet);self.accepted('accepted')
        # Even mutually agreeing transport cannot make the behavior commit a
        # reviewed final reporting packet that does not exist there.
        review['reporting_commit']=response['reporting_commit']=self.packet['behavior']
        self.state['external_review']=f.write(self.root,f.PACKET+'external-review.json',review)
        response['reporting_review_sha256']=self.state['external_review']['sha256']
        self.state['architect_acceptance']=f.write(self.root,f.PACKET+'architect-response.json',response);self.save()
        self.rejected('accepted reporting STATE missing')

    def test_earlier_pass_cannot_override_later_failure(self):
        later=copy.deepcopy(self.packet['review']);later.update(attempt='A-2',verdict='FAIL',supersedes='A-1')
        ref=f.write(self.root,f.PACKET+'attempt-2.json',later)
        self.state['stages'][0]['attempts'].append({'id':'A-2','subject_commit':self.packet['behavior'],
            'verdict':'FAIL','receipt':ref,'supersedes':'A-1','bindings':f.bindings(self.state)})
        self.save();self.rejected('effective attempt must be final attempt')

    def test_repair_pass_explicitly_supersedes_failure(self):
        f.fork_report(self.root,self.packet)
        first=copy.deepcopy(self.packet['review']);first['verdict']='FAIL'
        first_ref=f.write(self.root,f.PACKET+'attempt-1.json',first)
        self.packet['review'].update(attempt='A-2',supersedes='A-1')
        current_ref=f.write(self.root,f.PACKET+'review.json',self.packet['review'])
        self.packet['handoff']['review_sha256']=current_ref['sha256']
        self.state['handoff']=f.write(self.root,f.PACKET+'HANDOFF.json',self.packet['handoff'])
        self.state['stages'][0].update(effective='A-2',attempts=[
            {'id':'A-1','subject_commit':self.packet['behavior'],'verdict':'FAIL','receipt':first_ref,'supersedes':None,'bindings':f.bindings(self.state)},
            {'id':'A-2','subject_commit':self.packet['behavior'],'verdict':'PASS','receipt':current_ref,'supersedes':'A-1','bindings':f.bindings(self.state)}])
        self.save();self.accepted()
        self.state['stages'][0]['attempts'][-1]['supersedes']=None;self.save()
        self.rejected('repair supersession mismatch')

    def test_contract_changed_in_clean_descendant(self):
        self.packet['contract']['components']=['other']
        self.state['contract']=f.write(self.root,f.PACKET+'contract.json',self.packet['contract']);self.save()
        self.rejected('contract differs from frozen subject')

    def test_skip_worktree_does_not_hide_input(self):
        f.git(self.root,'update-index','--skip-worktree','runtime.py')
        (self.root/'runtime.py').write_text('changed\n')
        self.rejected('working input differs: runtime.py')

    def test_mode_delta_is_behavior(self):
        (self.root/'runtime.py').chmod(0o755);f.commit(self.root)
        self.rejected('unreviewed reporting delta: runtime.py')

    def test_missing_manifest_is_required(self):
        (self.root/f.PACKET/'inputs.json').unlink();f.commit(self.root)
        self.rejected('inputs.json missing')

    def test_malformed_manifest_digest(self):
        self.state['input_manifest']['sha256']='not-a-digest';self.save()
        self.rejected('input manifest digest must be lowercase SHA256')

    def test_unrelated_generation_commit(self):
        f.git(self.root,'checkout','--orphan','unrelated')
        f.git(self.root,'rm','-rf','.');f.write(self.root,'other','unrelated\n');other=f.commit(self.root)
        f.git(self.root,'checkout','-q',self.packet['reporting'])
        self.packet['evidence']['generation_commits']=[other]
        self.state['evidence_manifest']=f.write(self.root,f.PACKET+'evidence.json',self.packet['evidence']);self.save()
        self.rejected('generation subject not permitted')

    def test_self_referencing_manifest_forbidden(self):
        # Scope frozen in the behavior commit cannot be enlarged by a packet.
        evidence=self.packet['evidence'];evidence['files'][f.PACKET+'evidence.json']='0'*64
        self.state['evidence_manifest']=f.write(self.root,f.PACKET+'evidence.json',evidence);self.save()
        self.rejected('evidence file scope differs')

    def test_portable_packet_directory(self):
        temp=Path(self.temp.name)/'relocated'
        f.create(temp,packet_dir='review packet')
        result=subprocess.run([sys.executable,'-B',str(binding.DOCTOR),str(temp),
            '--packet-dir','review packet'],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('handoff / awaiting-architect',result.stdout)

    def test_repeated_command_arguments_are_valid(self):
        f.fork_report(self.root,self.packet)
        self.packet['evidence']['commands'][0]['argv']=['fixture-command','--x','value','--y','value']
        self.state['evidence_manifest']=f.write(self.root,f.PACKET+'evidence.json',self.packet['evidence'])
        self.packet['review']['evidence_manifest_sha256']=self.state['evidence_manifest']['sha256']
        self.packet['handoff']['evidence_manifest_sha256']=self.state['evidence_manifest']['sha256']
        f.write(self.root,f.PACKET+'review.json',self.packet['review']);f.reseal(self.root,self.packet,'review.json')
        self.accepted()

    def test_empty_command_argument_preserves_actual_argv(self):
        f.fork_report(self.root,self.packet)
        self.packet['evidence']['commands'][0]['argv']=['fixture-command','--empty-value','']
        f.reseal_all(self.root,self.packet)
        self.accepted()

    def test_pending_attempt_binds_current_subject(self):
        f.fork_report(self.root,self.packet)
        self.state.update(stage='review',handoff=None,handoff_status=None)
        attempt=self.state['stages'][0]['attempts'][0];attempt.update(verdict='PENDING',receipt=None)
        self.save();self.accepted('review')
        attempt['subject_commit']=self.packet['reporting'];self.save()
        self.rejected('active attempt subject mismatch')

    def test_accepted_reporting_packet_cannot_omit_stages(self):
        f.accepted_state(self.root,self.packet);self.accepted('accepted')
        valid=copy.deepcopy(self.state)
        # A real allowed reporting ancestor with an invalid stage list.
        self.state.update(handoff_status='awaiting-architect',external_review=None,architect_acceptance=None,stages=[])
        invalid_reporting=self.save()
        self.state=valid;self.packet['state']=valid
        self.packet['reporting']=invalid_reporting
        f.accepted_state(self.root,self.packet)
        self.rejected('accepted reporting packet invalid: stage scope differs')

    def test_accepted_reporting_packet_reads_immutable_evidence(self):
        f.accepted_state(self.root,self.packet);self.accepted('accepted')
        valid=copy.deepcopy(self.state)
        output=self.root/f.PACKET/'command.txt';original=output.read_bytes()
        self.state.update(handoff_status='awaiting-architect',external_review=None,architect_acceptance=None)
        output.write_text('Corrupted at the actual reporting subject\n')
        invalid_reporting=self.save()
        self.rejected('evidence file digest mismatch')
        output.write_bytes(original)
        self.state=valid;self.packet['state']=valid
        # Restored current bytes with the real valid prior F still pass.
        f.accepted_state(self.root,self.packet);self.accepted('accepted')
        self.packet['reporting']=invalid_reporting
        f.accepted_state(self.root,self.packet)
        self.rejected('accepted reporting packet invalid: evidence file digest mismatch')

    def test_accepted_reporting_state_wrong_type_has_bounded_diagnostic(self):
        f.accepted_state(self.root,self.packet);self.accepted('accepted')
        original=copy.deepcopy(self.state)
        f.write(self.root,f.PACKET+'STATE.json',[]);invalid=f.commit(self.root)
        f.save_state(self.root,original)
        self.packet['reporting']=invalid;f.accepted_state(self.root,self.packet)
        self.rejected('accepted reporting STATE must contain object')

    def test_intermediate_optional_reference_cannot_be_wrong_type(self):
        self.state.update(stage='implement',input_manifest=None,evidence_manifest=None,handoff=None,handoff_status=None)
        self.state['stages'][0]['attempts'][0].update(verdict='PENDING',receipt=None)
        self.save();self.accepted('implement')
        self.state['input_manifest']=False;self.save()
        self.rejected('input manifest reference fields differ')


if __name__=='__main__':unittest.main()
