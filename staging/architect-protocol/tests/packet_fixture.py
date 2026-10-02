"""Independent synthetic schema-2 Git packets; no Doctor implementation imports."""
import hashlib
import json
from pathlib import Path
import subprocess

PACKET='docs/architect/'

def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(root,name,value):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n' if not isinstance(value,str) else value)
    return {'path':name,'sha256':digest(path.read_bytes())}


def reference(root,name):
    return {'path':name,'sha256':digest((root/name).read_bytes())}


def bindings(state):
    return {key:state[key] for key in ('contract','input_manifest','evidence_manifest')}


def fork_report(root,packet):
    """One-property negative twin from B, separate from the passing F ancestry.

    Used only by synthetic controls that test a guard other than history. Never
    used by the history-preservation suite or on an implementation checkout.
    """
    git(root,'reset','--soft',packet['behavior'])


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


def commit(root):
    git(root,'add','-A')
    git(root,'-c','user.name=Synthetic Fixture','-c','user.email=fixture@example.invalid',
        'commit','--allow-empty','-qm','Synthetic test packet; no real approval')
    return git(root,'rev-parse','HEAD')


def create(root,phase='handoff',packet_dir='docs/architect',historical=None):
    prefix=packet_dir+'/'
    root.mkdir(parents=True);git(root,'init','-q')
    roles={'developer':'fixture-developer','reviewer':'fixture-reviewer','architect':'fixture-architect'}
    for name in ('PLAN.md','STAGES.md','ACCEPTANCE-MATRIX.md'):
        write(root,prefix+name,'# Synthetic fixture\nNarrative only; STATE.json is authoritative.\n')
    write(root,'runtime.py','print("fixture")\n')
    write(root,'.gitignore','*.pyc\ncache/\n')
    reporting=[prefix+n for n in ('STATE.json','inputs.json','evidence.json','command.txt',
        'review.json','HANDOFF.json','HANDOFF.md','external-review.json','architect-response.json',
        'optional-report.md','attempt-1.json','attempt-2.json')]
    contract={'schema':2,'kind':'architect-contract','scope':'all-tracked-except-reporting',
        'stages':['A'],'components':['core'],'findings':['R1'],'reporting_paths':reporting,
        'evidence_checks':[{'id':'verification','exit':0,'outputs':[prefix+'command.txt']}],
        'historical_stages':{}}
    if historical:
        historical(root,contract,roles)
    contract_ref=write(root,prefix+'contract.json',contract)
    behavior=commit(root)
    files={}
    for name in git(root,'ls-tree','-r','--name-only',behavior).splitlines():
        if name not in reporting:
            mode=git(root,'ls-tree',behavior,'--',name).split()[0]
            files[name]={'mode':mode,'sha256':digest((root/name).read_bytes())}
    tree=digest(''.join(name+':'+files[name]['mode']+':'+files[name]['sha256']+'\n' for name in sorted(files)).encode())
    inputs={'schema':2,'kind':'architect-inputs','subject_commit':behavior,'files':files,'tree_sha256':tree}
    input_ref=write(root,prefix+'inputs.json',inputs)
    output_ref=write(root,prefix+'command.txt','Synthetic successful command output\n')
    evidence={'schema':2,'kind':'architect-evidence','subject_commit':behavior,
        'contract_sha256':contract_ref['sha256'],'input_manifest_sha256':input_ref['sha256'],
        'generation_commits':[behavior],'files':{output_ref['path']:output_ref['sha256']},
        'commands':[{'id':'verification','argv':['fixture-command'],'cwd':'.',
            'environment':{'python':'synthetic','platform':'synthetic'},'exit':0,'outputs':[output_ref]}]}
    evidence_ref=write(root,prefix+'evidence.json',evidence)
    review={'schema':2,'kind':'architect-review','stage':'A','attempt':'A-1','verdict':'PASS',
        'subject_commit':behavior,'contract_sha256':contract_ref['sha256'],
        'input_manifest_sha256':input_ref['sha256'],'evidence_manifest_sha256':evidence_ref['sha256'],
        'evidence_generation_commits':[behavior],'reviewer_task':roles['reviewer'],
        'reviewed_at':'2026-09-22T00:00:00Z','supersedes':None}
    review_ref=write(root,prefix+'review.json',review)
    report_ref=write(root,prefix+'HANDOFF.md','# Synthetic handoff\nBehavior '+behavior+'\n')
    handoff={'schema':2,'kind':'architect-handoff','subject_commit':behavior,
        'contract_sha256':contract_ref['sha256'],'input_manifest_sha256':input_ref['sha256'],
        'evidence_manifest_sha256':evidence_ref['sha256'],'review_sha256':review_ref['sha256'],
        'components':{'core':'PASS'},'findings':{'R1':'CLOSED'},'report':report_ref,
        'residual_risks':['Synthetic fixture only'],'owner_decisions':['No real release authority']}
    handoff_ref=write(root,prefix+'HANDOFF.json',handoff)
    attempt={'id':'A-1','subject_commit':behavior,'verdict':'PASS','receipt':review_ref,'supersedes':None,
        'bindings':{'contract':contract_ref,'input_manifest':input_ref,'evidence_manifest':evidence_ref}}
    state={'schema':2,'protocol':'architect-protocol','mode':'production','stage':phase,
        'active_gate':'A','subject_commit':behavior,'subject_label':'Synthetic fixture',
        'roles':roles,'contract':contract_ref,'input_manifest':input_ref,'evidence_manifest':evidence_ref,
        'stages':[{'id':'A','attempts':[attempt],'effective':'A-1'}],
        'open_findings':[],'handoff':handoff_ref,'handoff_status':'awaiting-architect',
        'external_review':None,'architect_acceptance':None}
    if historical:
        state['active_gate']='G'
        state['stages']=[{'id':stage,'attempts':[{'id':stage+'-import',
            'subject_commit':item['subject_commit'],'verdict':'PASS','receipt':item['receipt'],
            'supersedes':None,'bindings':None}],'effective':stage+'-import'}
            for stage,item in contract['historical_stages'].items()]+state['stages']
        state['stages'][-1]['id']='G'
        state['stages'][-1]['attempts'][0]['id']='G-1'
        state['stages'][-1]['effective']='G-1'
        review.update(stage='G',attempt='G-1')
        state['stages'][-1]['attempts'][0]['receipt']=write(root,prefix+'review.json',review)
        handoff['review_sha256']=state['stages'][-1]['attempts'][0]['receipt']['sha256']
        state['handoff']=write(root,prefix+'HANDOFF.json',handoff)
    save_state(root,state,prefix)
    reporting_commit=commit(root)
    return {'state':state,'behavior':behavior,'reporting':reporting_commit,'contract':contract,
        'inputs':inputs,'evidence':evidence,'review':review,'handoff':handoff}


def save_state(root,state,prefix=PACKET):
    write(root,prefix+'STATE.json',state)


def reseal(root,packet,name):
    """Refresh only outer transport hashes so the semantic change is reached."""
    state=packet['state']
    if name=='review.json':
        ref=reference(root,PACKET+name);state['stages'][-1]['attempts'][-1]['receipt']=ref
        packet['handoff']['review_sha256']=ref['sha256']
        state['handoff']=write(root,PACKET+'HANDOFF.json',packet['handoff'])
    else:
        key={'inputs.json':'input_manifest','evidence.json':'evidence_manifest','HANDOFF.json':'handoff'}[name]
        state[key]=reference(root,PACKET+name)
    state['stages'][-1]['attempts'][-1]['bindings']=bindings(state)
    save_state(root,state);return commit(root)


def scope_state(example=False):
    return {'schema':2,'protocol':'architect-protocol','mode':'structural-example' if example else 'production',
        'stage':'scope','active_gate':None,'subject_commit':None,'subject_label':'Synthetic unfrozen scope',
        'roles':{'developer':'fixture-developer','reviewer':'fixture-reviewer','architect':'fixture-architect'},
        'contract':None,'input_manifest':None,'evidence_manifest':None,'stages':[],
        'open_findings':[],'handoff':None,'handoff_status':None,'external_review':None,'architect_acceptance':None}


def accepted_state(root,packet):
    review={'schema':2,'kind':'architect-reporting-review','behavior_commit':packet['behavior'],
        'reporting_commit':packet['reporting'],'verdict':'PASS','reviewer_task':'fixture-reviewer',
        'handoff_sha256':packet['state']['handoff']['sha256']}
    review_ref=write(root,PACKET+'external-review.json',review)
    response={'schema':2,'kind':'architect-acceptance','behavior_commit':packet['behavior'],
        'reporting_commit':packet['reporting'],'verdict':'PASS','components':{'core':'PASS'},
        'architect_task':'fixture-architect','reporting_review_sha256':review_ref['sha256']}
    response_ref=write(root,PACKET+'architect-response.json',response)
    state=packet['state'];state.update(handoff_status='accepted',external_review=review_ref,architect_acceptance=response_ref)
    save_state(root,state);commit(root)
    return review,response


# Refreeze synthetic behavior after changing a contract; outer hashes follow.
import copy
import sys
f=sys.modules[__name__]
def refreeze(root,p):
 s=p['state'];c=p['contract'];s['contract']=f.write(root,f.PACKET+'contract.json',c);behavior=f.commit(root)
 files={}
 for name in f.git(root,'ls-tree','-r','--name-only',behavior).splitlines():
  if name not in c['reporting_paths']:
   files[name]={'mode':f.git(root,'ls-tree',behavior,'--',name).split()[0],'sha256':f.digest((root/name).read_bytes())}
 m=p['inputs'];m.update(subject_commit=behavior,files=files,tree_sha256=f.digest(''.join(n+':'+files[n]['mode']+':'+files[n]['sha256']+'\n' for n in sorted(files)).encode()))
 s['input_manifest']=f.write(root,f.PACKET+'inputs.json',m)
 e=p['evidence'];e.update(subject_commit=behavior,contract_sha256=s['contract']['sha256'],input_manifest_sha256=s['input_manifest']['sha256'],generation_commits=[behavior])
 s['evidence_manifest']=f.write(root,f.PACKET+'evidence.json',e)
 r=p['review'];r.update(stage='B',attempt='B-1',supersedes=None,subject_commit=behavior,contract_sha256=s['contract']['sha256'],input_manifest_sha256=s['input_manifest']['sha256'],evidence_manifest_sha256=s['evidence_manifest']['sha256'],evidence_generation_commits=[behavior])
 rref=f.write(root,f.PACKET+'review.json',r)
 h=p['handoff'];h.update(subject_commit=behavior,contract_sha256=s['contract']['sha256'],input_manifest_sha256=s['input_manifest']['sha256'],evidence_manifest_sha256=s['evidence_manifest']['sha256'],review_sha256=rref['sha256'])
 h['report']=f.write(root,f.PACKET+'HANDOFF.md','# Synthetic handoff\nBehavior '+behavior+'\n');s['handoff']=f.write(root,f.PACKET+'HANDOFF.json',h)
 s.update(subject_commit=behavior,active_gate='B');s['stages'][-1]={'id':'B','effective':'B-1','attempts':[{'id':'B-1','subject_commit':behavior,'verdict':'PASS','receipt':rref,'supersedes':None,'bindings':bindings(s)}]}
 f.save_state(root,s);p.update(behavior=behavior,reporting=f.commit(root))

def history(root):
 p=f.create(root);old=copy.deepcopy(p)
 refs={}
 for name,key in [('contract','contract'),('input','inputs'),('evidence','evidence'),('review','review')]:
  refs[name]=f.write(root,f.PACKET+'historical-'+name+'.json',old[key])
 imp={'shape':'v2','receipt':refs['review'],'subject_commit':old['behavior'],'baseline_commit':None,'bindings':{'contract':refs['contract'],'input_manifest':refs['input'],'evidence_manifest':refs['evidence']},'prior_receipts':[]}
 p['contract']['stages']=['A','B'];p['contract']['historical_stages']={'A':imp};p['contract']['reporting_paths'] += [r['path'] for r in refs.values()]
 p['state']['stages']=[{'id':'A','effective':'A-1','attempts':[{'id':'A-1','subject_commit':old['behavior'],'verdict':'PASS','receipt':refs['review'],'supersedes':None,'bindings':None}]},{}]
 refreeze(root,p);return p,old['review']



def reseal_all(root,packet):
    """Refresh transport bindings after one semantic alteration, not expectations."""
    state=packet['state']
    state['input_manifest']=write(root,PACKET+'inputs.json',packet['inputs'])
    evidence=packet['evidence']
    evidence.update(contract_sha256=state['contract']['sha256'],input_manifest_sha256=state['input_manifest']['sha256'])
    state['evidence_manifest']=write(root,PACKET+'evidence.json',evidence)
    review=packet['review']
    review.update(contract_sha256=state['contract']['sha256'],input_manifest_sha256=state['input_manifest']['sha256'],
        evidence_manifest_sha256=state['evidence_manifest']['sha256'])
    state['stages'][-1]['attempts'][-1]['receipt']=write(root,PACKET+'review.json',review)
    handoff=packet['handoff']
    handoff.update(contract_sha256=state['contract']['sha256'],input_manifest_sha256=state['input_manifest']['sha256'],
        evidence_manifest_sha256=state['evidence_manifest']['sha256'],review_sha256=state['stages'][-1]['attempts'][-1]['receipt']['sha256'])
    state['handoff']=write(root,PACKET+'HANDOFF.json',handoff)
    state['stages'][-1]['attempts'][-1]['bindings']=bindings(state)
    save_state(root,state);commit(root)
