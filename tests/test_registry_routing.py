"""Public registry contract: invocation stages are distinct from activation.

Hand-authored rows and the shipped personalized template are consumed by the
real CLI. Instruction-use behavior is separately observed in fresh contexts.
"""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
CHECK=ROOT/'scripts/skill-registry.py'
HEADER='| Name | Trigger | Lifecycle | Workflow stages | Inputs | Outputs/Evidence | Reviewer/Gate | Required | Location | Version | Content-ID | Missing-capability |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n'


class RegistryRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='registry routing ')
        self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        target=self.root/'skills/example-skill';target.mkdir(parents=True)
        content=b'---\nname: example-skill\ndescription: Use when this disposable fixture is explicitly requested.\n---\n'
        (target/'SKILL.md').write_bytes(content)
        self.digest=hashlib.sha256(b'SKILL.md\0'+content+b'\0').hexdigest()
        (self.root/'docs').mkdir();self.path=self.root/'docs/SKILL-REGISTRY.md'
        self.fields=['example-skill','explicit fixture request','staged','Bootstrap, Close',
                     'fixture records','fixture report','independent review','optional',
                     'skills/example-skill','1.0.0','sha256:'+self.digest,'continue core and report unavailable fixture']
        self.write(self.fields);self.check(0,'PASS skill-registry')

    def write(self,fields):
        self.path.write_text(HEADER+'| '+' | '.join(fields)+' |\n')

    def check(self,code,diagnostic,script=CHECK):
        result=subprocess.run([sys.executable,'-B',str(script),str(self.root)],capture_output=True,text=True)
        self.assertEqual(result.returncode,code,result.stdout+result.stderr)
        self.assertIn(diagnostic,result.stdout);self.assertNotIn('Traceback',result.stderr)

    def test_personalized_shipped_template_is_accepted(self):
        template=(ROOT/'templates/SKILL-REGISTRY.md').read_text()
        self.path.write_text(template.replace('REPLACE_WITH_TREE_DIGEST',self.digest))
        self.check(0,'PASS skill-registry')

    def test_workflow_is_independent_of_lifecycle(self):
        for lifecycle in ('active','staged','retired'):
            fields=self.fields.copy();fields[2]=lifecycle;fields[3]='Triage, Review draft'
            self.write(fields);self.check(0,'PASS skill-registry')

    def test_empty_workflow_is_rejected(self):
        fields=self.fields.copy();fields[3]='';self.write(fields)
        self.check(1,'workflow stages is empty')

    def test_empty_stage_in_list_is_rejected(self):
        fields=self.fields.copy();fields[3]='Bootstrap, , Close';self.write(fields)
        self.check(1,'workflow stages contains empty stage')

    def test_activation_tokens_cannot_replace_invocation_stages(self):
        for value in ('active','staged','retired','Bootstrap, staged'):
            fields=self.fields.copy();fields[3]=value;self.write(fields)
            self.check(1,'workflow stages must describe invocation, not lifecycle')

    def test_old_header_without_workflow_is_rejected(self):
        old_header=HEADER.replace(' Workflow stages |','').replace('| --- |','',1)
        fields=self.fields[:3]+self.fields[4:]
        self.path.write_text(old_header+'| '+' | '.join(fields)+' |\n')
        self.check(1,'missing canonical registry header')

    def test_empty_workflow_guard_removal_is_effective(self):
        fields=self.fields.copy();fields[3]='';self.write(fields)
        self.check(1,'workflow stages is empty')
        script=self.root/'empty-guard-mutant.py';source=CHECK.read_text()
        guard='("workflow stages",workflow),'
        self.assertEqual(source.count(guard),1)
        # Keep the separate empty-list-member guard; it applies to nonempty lists.
        script.write_text(source.replace(guard,''))
        self.write(self.fields);self.check(0,'PASS skill-registry',script)
        self.write(fields);self.check(0,'PASS skill-registry',script)

    def test_lifecycle_separation_guard_removal_is_effective(self):
        fields=self.fields.copy();fields[3]='staged';self.write(fields)
        self.check(1,'workflow stages must describe invocation, not lifecycle')
        script=self.root/'lifecycle-guard-mutant.py';source=CHECK.read_text()
        guard='if any(stage.lower() in STATUSES for stage in stages):'
        self.assertEqual(source.count(guard),1)
        script.write_text(source.replace(guard,'if False:'))
        self.write(self.fields);self.check(0,'PASS skill-registry',script)
        self.write(fields);self.check(0,'PASS skill-registry',script)

    def test_empty_list_member_guard_removal_is_effective(self):
        fields=self.fields.copy();fields[3]='Bootstrap, , Close';self.write(fields)
        self.check(1,'workflow stages contains empty stage')
        script=self.root/'list-member-guard-mutant.py';source=CHECK.read_text()
        guard='if not all(stages):'
        self.assertEqual(source.count(guard),1)
        script.write_text(source.replace(guard,'if False:'))
        self.write(self.fields);self.check(0,'PASS skill-registry',script)
        self.write(fields);self.check(0,'PASS skill-registry',script)


if __name__=='__main__':unittest.main()
