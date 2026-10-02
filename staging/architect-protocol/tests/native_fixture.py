#!/usr/bin/env python3
"""Generate synthetic native attempts with genuine differing subjects/triples.

No Doctor imports or approval claims. Each command executes the differing
frozen runtime; all receipts are explicitly synthetic. The optional mutation
hook runs before the final freeze so binding tests do not alter declared
completed attempts within the selected current contract history.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

P='docs/architect/'
IDS=('A-1','G-1','G-2','G-3')
ROLES={'developer':'synthetic-developer','reviewer':'synthetic-reviewer','architect':'synthetic-architect'}

def sha(data):return hashlib.sha256(data).hexdigest()

def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()

def write(root,name,value):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode() if not isinstance(value,bytes) else value
    path.write_bytes(data);return {'path':name,'sha256':sha(data)}

def commit(root,message):
    git(root,'add','-A')
    git(root,'-c','user.name=Synthetic Fixture','-c','user.email=fixture@example.invalid','commit','-qm',message)
    return git(root,'rev-parse','HEAD')

def entries(root,revision):
    raw=subprocess.check_output(['git','-C',str(root),'ls-tree','-r','-z',revision])
    result={}
    for row in raw.split(b'\0'):
        if row:
            meta,path=row.split(b'\t',1);mode,kind,oid=meta.decode().split()
            assert kind=='blob';result[path.decode()]={'mode':mode,'oid':oid}
    return result

def blob(root,revision,path):
    return subprocess.check_output(['git','-C',str(root),'show',revision+':'+path])

def build(root,bindings_key="bindings",before_freeze=None,original_contract=None,runtime_exits=None):
    assert not root.exists(), 'Output must be a new disposable directory'
    root.mkdir(parents=True);git(root,'init','-q')
    for name in ('PLAN.md','STAGES.md','ACCEPTANCE-MATRIX.md'):
        write(root,P+name,b'# Synthetic fixture\nSTATE.json is authoritative. No actual approval.\n')
    write(root,'.gitignore',b'*.pyc\n')
    reporting=[P+n for n in ('STATE.json','HANDOFF.json','HANDOFF.md','external-review.json','architect-response.json','optional-report.md')]
    for attempt in IDS:
        reporting += [P+'attempts/'+attempt+'/'+name for name in ('inputs.json','evidence.json','review.json','stdout.txt')]
    contracts={}
    for attempt in IDS:
        value={'schema':2,'kind':'architect-contract','scope':'all-tracked-except-reporting',
            'stages':['A','G'],'components':['core'],'findings':['R1'],
            'reporting_paths':reporting,'historical_stages':{},
            'evidence_checks':[{'id':'runtime-output','exit':0,'outputs':[P+'attempts/'+attempt+'/stdout.txt']}]}
        if original_contract:original_contract(attempt,value)
        contracts[attempt]=(value,write(root,P+'contracts/'+attempt+'.json',value))
    completed={};subjects={};reporting_commits={};observations=[]
    runtime_exits={} if runtime_exits is None else runtime_exits
    assert set(runtime_exits)<=set(IDS) and all(type(code) is int for code in runtime_exits.values())

    def runtime(attempt,source):
        if attempt in runtime_exits:
            source+=('raise SystemExit('+str(runtime_exits[attempt])+')\n').encode()
        write(root,'runtime.py',source)

    def make_attempt(attempt,subject,verdict,supersedes):
        contract,cref=contracts[attempt];prefix=P+'attempts/'+attempt+'/'
        tracked=entries(root,subject);files={}
        for name,info in tracked.items():
            if name not in reporting:
                files[name]={'mode':info['mode'],'sha256':sha(blob(root,subject,name))}
        manifest={'schema':2,'kind':'architect-inputs','subject_commit':subject,'files':files,
            'tree_sha256':sha(''.join(n+':'+files[n]['mode']+':'+files[n]['sha256']+'\n' for n in sorted(files)).encode())}
        mref=write(root,prefix+'inputs.json',manifest)
        command=[sys.executable,'-B','runtime.py']
        execution=subprocess.run(command,cwd=root,capture_output=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        assert execution.returncode==runtime_exits.get(attempt,0) and not execution.stderr
        outref=write(root,prefix+'stdout.txt',execution.stdout)
        evidence={'schema':2,'kind':'architect-evidence','subject_commit':subject,
            'contract_sha256':cref['sha256'],'input_manifest_sha256':mref['sha256'],
            'generation_commits':[subject],'files':{outref['path']:outref['sha256']},
            'commands':[{'id':'runtime-output','argv':command,'cwd':'.',
                'environment':{'python':platform.python_version(),'platform':platform.platform()},
                'exit':execution.returncode,'outputs':[outref]}]}
        eref=write(root,prefix+'evidence.json',evidence)
        raw={'schema':2,'kind':'architect-review','stage':attempt.split('-')[0],'attempt':attempt,
            'verdict':verdict,'subject_commit':subject,'contract_sha256':cref['sha256'],
            'input_manifest_sha256':mref['sha256'],'evidence_manifest_sha256':eref['sha256'],
            'evidence_generation_commits':[subject],'reviewer_task':ROLES['reviewer'],
            'reviewed_at':'2026-09-22T00:00:00Z','supersedes':supersedes}
        rref=write(root,prefix+'review.json',raw)
        triple={'contract':cref,'input_manifest':mref,'evidence_manifest':eref}
        record={'id':attempt,'subject_commit':subject,'verdict':verdict,'receipt':rref,'supersedes':supersedes,bindings_key:triple}
        completed[attempt]={'record':record,'triple':triple,'raw':raw,'command_output':outref}
        observations.append({'attempt':attempt,'argv':command,'exit':execution.returncode,'stdout_sha256':outref['sha256']})
        return record

    def state(current,subject,g_attempts,phase):
        contract,cref=contracts[current]
        item=completed.get(current)
        final=phase=='handoff'
        s={'schema':2,'protocol':'architect-protocol','mode':'production','stage':phase,'active_gate':'G',
            'subject_commit':subject,'subject_label':'Synthetic differing-subject fixture','roles':ROLES,
            'contract':cref,'input_manifest':item['triple']['input_manifest'] if item else None,
            'evidence_manifest':item['triple']['evidence_manifest'] if item else None,
            'stages':[{'id':'A','attempts':[completed['A-1']['record']],'effective':'A-1'},
                {'id':'G','attempts':g_attempts,'effective':g_attempts[-1]['id']}],
            'open_findings':[] if final else ['R1'],'handoff':None,'handoff_status':None,
            'external_review':None,'architect_acceptance':None}
        if final:
            report=write(root,P+'HANDOFF.md',('# Synthetic handoff\nBehavior '+subject+'\n').encode())
            h={'schema':2,'kind':'architect-handoff','subject_commit':subject,
                'contract_sha256':cref['sha256'],'input_manifest_sha256':s['input_manifest']['sha256'],
                'evidence_manifest_sha256':s['evidence_manifest']['sha256'],'review_sha256':item['record']['receipt']['sha256'],
                'components':{'core':'PASS'},'findings':{'R1':'CLOSED'},'report':report,
                'residual_risks':['Synthetic fixture; no actual review authority'],'owner_decisions':[]}
            s.update(handoff=write(root,P+'HANDOFF.json',h),handoff_status='awaiting-architect')
        write(root,P+'STATE.json',s);return s

    runtime('A-1',b'print("A original behavior")\n')
    subjects['A-1']=commit(root,'Synthetic A behavior freeze')
    a=make_attempt('A-1',subjects['A-1'],'PASS',None)
    pending={'id':'G-1','subject_commit':subjects['A-1'],'verdict':'PENDING','receipt':None,'supersedes':None,bindings_key:None}
    state('G-1',subjects['A-1'],[pending],'implement')
    reporting_commits['A-1']=commit(root,'Retain original A PASS and pending G attempt')

    runtime('G-1',b'print("G first implementation")\n')
    subjects['G-1']=commit(root,'Synthetic G first distinct behavior freeze')
    g1=make_attempt('G-1',subjects['G-1'],'PASS',None)
    state('G-1',subjects['G-1'],[g1],'handoff')
    reporting_commits['G-1']=commit(root,'Retain original G-1 PASS')

    runtime('G-2',b'print("G issue discovered in changed implementation")\n')
    subjects['G-2']=commit(root,'Synthetic G second distinct behavior freeze')
    g2=make_attempt('G-2',subjects['G-2'],'FAIL','G-1')
    state('G-2',subjects['G-2'],[g1,g2],'repair')
    reporting_commits['G-2']=commit(root,'Retain original G-2 FAIL without rewriting G-1')

    # Seed the known completed chain at final B under the exact current contract.
    # Earlier contract boundaries are explicit; the final strict history scan
    # has G-2 in its own B snapshot and cannot lose it by scanning from final B.
    if before_freeze:
        before_freeze(root,completed,subjects,contracts)
    state('G-3',subjects['G-2'],[g1,g2],'repair')
    runtime('G-3',b'print("G repaired implementation")\n')
    subjects['G-3']=commit(root,'Freeze repaired behavior with committed original attempt history')
    g3=make_attempt('G-3',subjects['G-3'],'PASS','G-2')
    final=state('G-3',subjects['G-3'],[g1,g2,g3],'handoff')
    reporting_commits['G-3']=commit(root,'Retain G-3 repair PASS and current handoff')

    return {'state':final,'completed':completed,'subjects':subjects,
        'behavior':subjects['G-3'],'reporting':reporting_commits['G-3'],
        'contracts':contracts,'observations':observations}
