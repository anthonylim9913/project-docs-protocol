"""Portable schema-2 packet validation. Hashes establish identity, not authority."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

LIFECYCLE=('scope','baseline','implement','review','repair','handoff')
VERDICTS=('PENDING','PASS','FAIL','FAIL — verification incomplete')
SHA=re.compile(r'[0-9a-f]{64}')
COMMIT=re.compile(r'[0-9a-f]{40}')


class Invalid(ValueError):
    pass


def need(condition,message):
    if not condition:raise Invalid(message)


def text(value,label):
    need(isinstance(value,str) and bool(value.strip()),label+' must be a nonempty string')
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(value,label):
    need(isinstance(value,str) and SHA.fullmatch(value) is not None,label+' must be lowercase SHA256')
    return value


def exact(value,keys,label):
    need(isinstance(value,dict) and set(value)==set(keys),label+' fields differ')
    return value


def names(value,label,nonempty=True):
    need(isinstance(value,list) and (bool(value) or not nonempty),label+' must be a list')
    for item in value:text(item,label+' item')
    need(len(value)==len(set(value)),label+' contains duplicates')
    return value


def path_parts(value):
    text(value,'artifact path')
    need(not any(c in value for c in '\\:\n\r\0*?[') and not value.startswith('/')
        and all(p not in ('','.','..','.git') for p in value.split('/')),'invalid project-relative artifact path: '+repr(value))
    return value.split('/')


def load_json(data,label):
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'duplicate JSON key in '+label+': '+key)
            result[key]=value
        return result
    try:return json.loads(data.decode('utf-8'),object_pairs_hook=pairs,
        parse_constant=lambda value:(_ for _ in ()).throw(Invalid('invalid JSON constant '+value)))
    except (UnicodeError,json.JSONDecodeError) as error:raise Invalid(label+' is not valid UTF-8 JSON: '+str(error))


class Project:
    def __init__(self,root):
        self.root=Path(root).resolve()
        need(hasattr(os,'O_NOFOLLOW') and hasattr(os,'O_DIRECTORY') and hasattr(os,'O_NONBLOCK')
            and os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd,
            'safe descriptor operations unavailable; packet read refused')

    @contextmanager
    def directory(self,parts):
        chain=[];fd=os.open(str(self.root),os.O_RDONLY|os.O_DIRECTORY)
        start=fd
        try:
            for name in parts:
                info=os.stat(name,dir_fd=fd,follow_symlinks=False)
                need(not stat.S_ISLNK(info.st_mode),'symlinked artifact: '+name)
                need(stat.S_ISDIR(info.st_mode),'artifact parent must be directory: '+name)
                child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
                held=os.fstat(child);chain.append((child,fd,name))
                need((info.st_dev,info.st_ino)==(held.st_dev,held.st_ino),'artifact parent identity changed')
                fd=child
            yield fd
            visible=self.root.stat();held=os.fstat(start)
            need((visible.st_dev,visible.st_ino)==(held.st_dev,held.st_ino),'project identity changed')
            for child,parent,name in chain:
                actual=os.fstat(child);visible=os.stat(name,dir_fd=parent,follow_symlinks=False)
                need((actual.st_dev,actual.st_ino)==(visible.st_dev,visible.st_ino),'artifact parent identity changed')
        finally:
            for child,_,_ in reversed(chain):os.close(child)
            os.close(start)

    def read(self,name):
        parts=path_parts(name)
        try:
            with self.directory(parts[:-1]) as parent:
                before=os.stat(parts[-1],dir_fd=parent,follow_symlinks=False)
                need(not stat.S_ISLNK(before.st_mode),'symlinked artifact: '+name)
                need(stat.S_ISREG(before.st_mode) and before.st_nlink==1,'artifact must be regular and single-link: '+name)
                fd=os.open(parts[-1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
                try:
                    actual=os.fstat(fd)
                    need((before.st_dev,before.st_ino)==(actual.st_dev,actual.st_ino),'artifact identity changed: '+name)
                    data=[]
                    while True:
                        block=os.read(fd,65536)
                        if not block:break
                        data.append(block)
                    after=os.stat(parts[-1],dir_fd=parent,follow_symlinks=False)
                    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
                        (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'artifact changed during read: '+name)
                    return b''.join(data)
                finally:os.close(fd)
        except FileNotFoundError:raise Invalid(name+' missing')

    def ref(self,ref,label,json_data=False):
        exact(ref,('path','sha256'),label+' reference');sha(ref['sha256'],label+' digest')
        data=self.read(ref['path'])
        need(digest(data)==ref['sha256'],label+' digest mismatch')
        return load_json(data,label) if json_data else data

    def git(self,*args,check=True):
        result=subprocess.run(['git','-C',str(self.root),*args],capture_output=True)
        if check:need(result.returncode==0,'Git command failed: '+args[0])
        return result

    def head(self):
        return self.git('rev-parse','HEAD').stdout.decode().strip()

    def mode(self,name):
        return '100755' if (self.root/name).stat().st_mode & 0o111 else '100644'

    def has(self,name):
        return (self.root/name).exists() or (self.root/name).is_symlink()

    def commit(self,value,label):
        need(isinstance(value,str) and COMMIT.fullmatch(value) is not None,label+' requires full immutable subject')
        result=self.git('rev-parse','--verify',value+'^{commit}',check=False)
        need(result.returncode==0 and result.stdout.decode().strip()==value,label+' commit unresolved')
        return value

    def ancestor(self,old,new):
        return self.git('merge-base','--is-ancestor',old,new,check=False).returncode==0

    def blobs(self,revision):
        result={}
        for row in self.git('ls-tree','-r','-z',revision).stdout.split(b'\0'):
            if not row:continue
            meta,name=row.split(b'\t',1);mode,kind,oid=meta.decode().split();name=name.decode('utf-8');path_parts(name)
            need(kind=='blob' and mode in ('100644','100755'),'unsupported Git input type: '+name)
            result[name]={'mode':mode,'oid':oid}
        return result

    def blob(self,revision,name):
        path_parts(name);return self.git('show',revision+':'+name).stdout

    def delta(self,subject,head,allowed):
        need(self.ancestor(subject,head),'subject is not ancestor of HEAD')
        changed=self.git('diff','--name-only','--no-renames','-z',subject,head).stdout.decode('utf-8').split('\0')
        for name in changed:
            if name:need(name in allowed,'unreviewed reporting delta: '+name)

    def clean(self,head):
        untracked=self.git('ls-files','--others','--directory','-z').stdout.decode('utf-8').split('\0')
        need(not any(untracked),'untracked path: '+next((p for p in untracked if p),''))
        for name,meta in self.blobs(head).items():
            data=self.read(name)
            need(data==self.git('cat-file','blob',meta['oid']).stdout,'working tracked file differs: '+name)
            mode=self.mode(name)
            need(mode==meta['mode'],'working tracked mode differs: '+name)


def schema(value,kind,label):
    need(isinstance(value,dict),label+' must contain object')
    need(type(value.get('schema')) is int and value['schema']==2,label+' requires schema 2')
    need(value.get('kind')==kind,label+' kind mismatch')


def contract_check(contract,ref):
    schema(contract,'architect-contract','contract')
    exact(contract,('schema','kind','scope','stages','components','findings','reporting_paths','evidence_checks','historical_stages'),'contract')
    need(contract['scope']=='all-tracked-except-reporting','unsupported input scope')
    for key in ('stages','components','findings','reporting_paths'):names(contract[key],key,nonempty=key!='findings')
    for name in contract['reporting_paths']:path_parts(name)
    need(ref['path'] not in contract['reporting_paths'],'contract cannot be reporting')
    need(isinstance(contract['historical_stages'],dict),'historical_stages must be object')
    need(set(contract['historical_stages']) <= set(contract['stages'][:-1]),'final stage cannot use historical compatibility')
    checks=contract['evidence_checks'];need(isinstance(checks,list) and bool(checks),'required evidence checks missing')
    ids=[];paths=[]
    for check in checks:
        exact(check,('id','exit','outputs'),'evidence check');ids.append(text(check['id'],'check id'))
        need(type(check['exit']) is int,'check exit must be integer')
        for name in names(check['outputs'],'check outputs'):
            path_parts(name);need(name in contract['reporting_paths'],'evidence output not declared reporting: '+name);paths.append(name)
    need(len(ids)==len(set(ids)),'duplicate evidence check')
    need(len(paths)==len(set(paths)),'duplicate evidence output')


def inputs_check(project,subject,contract,ref,current=True):
    manifest=project.ref(ref,'input manifest',True);schema(manifest,'architect-inputs','input manifest')
    exact(manifest,('schema','kind','subject_commit','files','tree_sha256'),'input manifest')
    need(manifest['subject_commit']==subject,'input manifest subject mismatch')
    actual=project.blobs(subject);expected={p for p in actual if p not in contract['reporting_paths']}
    files=manifest['files'];need(isinstance(files,dict) and set(files)==expected,'input scope differs')
    rows=[]
    for name in sorted(expected):
        info=exact(files[name],('mode','sha256'),'input entry');sha(info['sha256'],'input hash')
        need(info['mode']==actual[name]['mode'],'input Git mode mismatch: '+name)
        blob=project.git('cat-file','blob',actual[name]['oid']).stdout
        need(info['sha256']==digest(blob),'input differs from reviewed subject: '+name)
        if current:
            need(project.read(name)==blob,'working input differs: '+name)
            mode=project.mode(name)
            need(mode==info['mode'],'working input mode differs: '+name)
        rows.append(name+':'+info['mode']+':'+info['sha256']+'\n')
    need(manifest['tree_sha256']==digest(''.join(rows).encode()),'input tree digest mismatch')
    return manifest


def generation_check(project,values,subject,allowed):
    for value in names(values,'evidence generation commits'):
        project.commit(value,'generation')
        need(project.ancestor(subject,value),'generation subject not permitted')
        project.delta(subject,value,allowed)


def evidence_check(project,state,contract,require_expected=True):
    result=project.ref(state['evidence_manifest'],'evidence manifest',True);schema(result,'architect-evidence','evidence manifest')
    exact(result,('schema','kind','subject_commit','contract_sha256','input_manifest_sha256','generation_commits','files','commands'),'evidence manifest')
    need(result['subject_commit']==state['subject_commit'],'evidence subject mismatch')
    for field,key in [('contract_sha256','contract'),('input_manifest_sha256','input_manifest')]:
        need(result[field]==state[key]['sha256'],'evidence '+field+' mismatch')
    generation_check(project,result['generation_commits'],state['subject_commit'],contract['reporting_paths'])
    required={p for check in contract['evidence_checks'] for p in check['outputs']}
    need(isinstance(result['files'],dict) and set(result['files'])==required,'evidence file scope differs')
    need(state['evidence_manifest']['path'] not in required,'evidence manifest self reference')
    for name,value in result['files'].items():project.ref({'path':name,'sha256':value},'evidence file')
    commands=result['commands'];need(isinstance(commands,list),'evidence commands must be list')
    need(len(commands)==len(contract['evidence_checks']),'evidence command scope differs')
    for command,expected in zip(commands,contract['evidence_checks']):
        exact(command,('id','argv','cwd','environment','exit','outputs'),'evidence command')
        need(command['id']==expected['id'],'evidence command scope differs')
        need(isinstance(command['argv'],list) and bool(command['argv']),'command argv must be nonempty list')
        text(command['argv'][0],'command executable')
        for argument in command['argv']:
            need(isinstance(argument,str),'command argument must be string')
        text(command['cwd'],'command cwd')
        exact(command['environment'],('python','platform'),'command environment')
        for value in command['environment'].values():text(value,'environment value')
        need(type(command['exit']) is int,'evidence command exit must be integer')
        if require_expected:
            need(command['exit']==expected['exit'],'evidence command exit mismatch')
        wanted=[{'path':p,'sha256':result['files'][p]} for p in expected['outputs']]
        need(command['outputs']==wanted,'evidence command outputs mismatch')
    return result


def review_shape(project,result,state,label):
    schema(result,'architect-review',label)
    exact(result,('schema','kind','stage','attempt','verdict','subject_commit','contract_sha256','input_manifest_sha256',
        'evidence_manifest_sha256','evidence_generation_commits','reviewer_task','reviewed_at','supersedes'),label)
    project.commit(result['subject_commit'],label+' subject')
    for key in ('contract_sha256','input_manifest_sha256','evidence_manifest_sha256'):sha(result[key],label+' '+key)
    for key in ('stage','attempt','reviewed_at'):text(result[key],label+' '+key)
    need(result['verdict'] in VERDICTS[1:],label+' completed verdict invalid')
    need(result['reviewer_task']==state['roles']['reviewer'],label+' reviewer task mismatch')
    if result['supersedes'] is not None:text(result['supersedes'],label+' supersedes')
    for value in names(result['evidence_generation_commits'],label+' generation commits'):
        project.commit(value,'generation')


def current_review(project,ref,state,gate,attempt,evidence,final):
    result=project.ref(ref,'reviewer receipt',True)
    review_shape(project,result,state,'reviewer receipt')
    need(result['subject_commit']==attempt['subject_commit'],'reviewer subject mismatch')
    need(result['stage']==gate and result['attempt']==attempt['id'],'reviewer stage/attempt mismatch')
    need(result['verdict']==attempt['verdict'],'reviewer verdict mismatch')
    need(result['reviewer_task']==state['roles']['reviewer'],'reviewer task mismatch')
    need(result['supersedes']==attempt['supersedes'],'repair supersession mismatch')
    bindings=exact(attempt['bindings'],('contract','input_manifest','evidence_manifest'),'native attempt bindings')
    for field,key in [('contract_sha256','contract'),('input_manifest_sha256','input_manifest'),('evidence_manifest_sha256','evidence_manifest')]:
        exact(bindings[key],('path','sha256'),'native '+key+' reference')
        need(result[field]==bindings[key]['sha256'],'reviewer '+field+' mismatch')
    own_contract=project.ref(bindings['contract'],'native contract',True)
    contract_check(own_contract,bindings['contract'])
    need(gate in own_contract['stages'] and gate not in own_contract['historical_stages'],
        'native stage absent from original contract scope')
    need(project.blob(attempt['subject_commit'],bindings['contract']['path'])==project.read(bindings['contract']['path']),
        'native contract differs from original subject')
    inputs_check(project,attempt['subject_commit'],own_contract,bindings['input_manifest'],current=False)
    own_state=dict(bindings,subject_commit=attempt['subject_commit'])
    # Only the validated receipt verdict permits a complete failed observation.
    # Every PASS (including earlier attempts) still meets its own frozen exits.
    own_evidence=evidence_check(project,own_state,own_contract,require_expected=result['verdict']=='PASS')
    generation_check(project,result['evidence_generation_commits'],attempt['subject_commit'],own_contract['reporting_paths'])
    need(result['evidence_generation_commits']==own_evidence['generation_commits'],'reviewer generation mismatch')
    if final:
        need(result['subject_commit']==state['subject_commit'],'reviewer subject mismatch')
        need(bindings=={key:state[key] for key in bindings},'final native bindings differ from current STATE')
    return result


def historical_review(project,imported,stage,state,record):
    exact(imported,('shape','receipt','subject_commit','baseline_commit','bindings','prior_receipts'),'historical import')
    need(imported['shape'] in ('legacy-a','legacy-b','legacy-c','v2'),'unsupported historical receipt shape')
    project.commit(imported['subject_commit'],'historical subject')
    need(len(record['attempts'])==1,'frozen historical stage attempts changed')
    attempt=record['attempts'][0]
    need(attempt['bindings'] is None,'historical attempts use frozen contract bindings')
    need(attempt['receipt']==imported['receipt'] and attempt['subject_commit']==imported['subject_commit'],
        'frozen historical receipt selection changed')
    raw=project.ref(imported['receipt'],'historical receipt',True)
    need(isinstance(raw,dict),'historical receipt must be object')
    for key,value in [('stage',stage),('verdict','PASS'),('reviewer_task',state['roles']['reviewer'])]:
        need(raw.get(key)==value,'historical '+key+' mismatch')
    shape=imported['shape']
    if shape in ('legacy-a','legacy-b'):
        need(type(raw.get('schema')) is int and raw['schema']==1
            and raw.get('kind')=='independent-stage-review','historical legacy schema/kind mismatch')
    elif shape=='legacy-c':
        need('schema' not in raw and 'kind' not in raw,'historical legacy-c shape mismatch')
    field='packet_commit' if shape=='legacy-a' else 'subject_commit'
    need(raw.get(field)==imported['subject_commit'],'historical subject mismatch')
    need(('subject_commit' not in raw if shape=='legacy-a' else 'packet_commit' not in raw),'conflicting historical subject fields')
    if shape=='legacy-a':
        need(raw.get('baseline_behavior_commit')==imported['baseline_commit'],'historical baseline mismatch')
        project.commit(imported['baseline_commit'],'historical baseline')
        manifest=raw.get('baseline_input_manifest');need(isinstance(manifest,dict),'historical manifest binding missing')
        bindings={'input_manifest':manifest.get('sha256')}
    elif shape=='legacy-b':
        need(imported['baseline_commit'] is None,'unexpected historical baseline')
        manifest=raw.get('input_manifest');need(isinstance(manifest,dict),'historical manifest binding missing')
        bindings={'input_manifest':manifest.get('sha256')}
    elif shape=='legacy-c':
        need(imported['baseline_commit'] is None,'unexpected historical baseline')
        bindings={'input_manifest':raw.get('submitted_manifest_sha256')}
    else:
        review_shape(project,raw,state,'historical v2 receipt')
        need(raw['attempt']==attempt['id'],'historical attempt mismatch')
        need(imported['baseline_commit'] is None,'unexpected historical baseline')
        bindings={key:raw.get(field) for key,field in [('contract','contract_sha256'),('input_manifest','input_manifest_sha256'),('evidence_manifest','evidence_manifest_sha256')]}
    # Old receipts that supplied a contract digest must retain that binding too.
    if shape!='v2' and 'acceptance_contract_hash' in raw:bindings['contract']=raw['acceptance_contract_hash']
    need(isinstance(imported['bindings'],dict) and set(imported['bindings'])==set(bindings),'historical artifact binding scope differs')
    for key,value in bindings.items():
        sha(value,'original historical '+key)
        ref=imported['bindings'][key]
        project.ref(ref,'historical '+key)
        need(ref['sha256']==value,'original historical '+key+' digest mismatch')
    need(isinstance(imported['prior_receipts'],list),'prior receipts must be list')
    prior_ids=[]
    for ref in imported['prior_receipts']:
        prior=project.ref(ref,'prior historical receipt',True)
        allowed=VERDICTS[1:] if shape=='v2' else ('FAIL','FAIL — verification incomplete')
        need(isinstance(prior,dict) and prior.get('stage')==stage and prior.get('verdict') in allowed,
            'prior historical completed review mismatch')
        if shape=='v2':
            review_shape(project,prior,state,'prior v2 receipt')
            prior_ids.append(text(prior.get('attempt'),'prior attempt'))
            need(prior.get('supersedes')==(prior_ids[-2] if len(prior_ids)>1 else None),'historical prior supersession mismatch')
    if shape=='v2':
        need(len(set(prior_ids+[raw['attempt']]))==len(prior_ids)+1,'duplicate historical attempt')
        need(raw['supersedes']==(prior_ids[-1] if prior_ids else None),'historical supersession mismatch')
        old_contract=project.ref(imported['bindings']['contract'],'historical contract',True)
        contract_check(old_contract,imported['bindings']['contract'])
        generation_check(project,raw['evidence_generation_commits'],imported['subject_commit'],old_contract['reporting_paths'])


def stages_check(project,state,contract,evidence):
    stages=state['stages'];need(isinstance(stages,list),'stages must be list')
    need([r.get('id') if isinstance(r,dict) else None for r in stages]==contract['stages'],'stage scope differs')
    need(state['active_gate'] in contract['stages'],'active gate absent from contract')
    active=contract['stages'].index(state['active_gate']);final=state['stage']=='handoff'
    if final:need(active==len(stages)-1,'handoff must complete final gate')
    for position,record in enumerate(stages):
        exact(record,('id','attempts','effective'),'stage record');attempts=record['attempts']
        need(isinstance(attempts,list),'attempts must be list')
        if not attempts:
            need(record['effective'] is None and position>active and not final,'required stage '+record['id']+' has no attempt')
            continue
        ids=[]
        for index,attempt in enumerate(attempts):
            exact(attempt,('id','subject_commit','verdict','receipt','supersedes','bindings'),'stage attempt')
            if attempt['bindings'] is not None:
                exact(attempt['bindings'],('contract','input_manifest','evidence_manifest'),'attempt bindings')
                for key,ref in attempt['bindings'].items():
                    exact(ref,('path','sha256'),'attempt '+key+' reference');path_parts(ref['path']);sha(ref['sha256'],'attempt '+key+' digest')
            ids.append(text(attempt['id'],'attempt id'));project.commit(attempt['subject_commit'],'attempt subject')
            need(attempt['verdict'] in VERDICTS,'invalid attempt verdict')
            expected=attempts[index-1]['id'] if index else None
            need(attempt['supersedes']==expected,'repair supersession mismatch')
        need(len(ids)==len(set(ids)),'duplicate attempt id')
        need(record['effective']==ids[-1],'effective attempt must be final attempt')
        last=attempts[-1]
        need(position<=active,'future stage cannot have an attempt')
        if position==active and state['stage'] in ('baseline','review','repair'):
            need(last['subject_commit']==state['subject_commit'],'active attempt subject mismatch')
        if final or position<active:need(last['verdict']=='PASS','required stage '+record['id']+' is not PASS')
        if record['id'] in contract['historical_stages']:
            need(position<active,'active gate cannot be a frozen historical stage')
            historical_review(project,contract['historical_stages'][record['id']],record['id'],state,record)
            continue
        for index,attempt in enumerate(attempts):
            if attempt['verdict']=='PENDING':
                need(attempt['receipt'] is None,'pending attempt cannot claim receipt')
            else:
                need(attempt['receipt'] is not None,'completed attempt requires receipt')
                current_review(project,attempt['receipt'],state,record['id'],attempt,evidence,
                    final and position==active and index==len(attempts)-1)
        if position==active:
            if state['stage']=='repair':need(last['verdict'] in ('FAIL','FAIL — verification incomplete'),'repair requires failed review')
            if state['stage'] in ('implement','review','baseline'):need(last['verdict']=='PENDING','intermediate active gate must be pending')


def handoff_check(project,state,contract,evidence):
    need(state['handoff'] is not None,'final HANDOFF required')
    result=project.ref(state['handoff'],'HANDOFF',True);schema(result,'architect-handoff','HANDOFF')
    exact(result,('schema','kind','subject_commit','contract_sha256','input_manifest_sha256','evidence_manifest_sha256',
        'review_sha256','components','findings','report','residual_risks','owner_decisions'),'HANDOFF')
    need(result['subject_commit']==state['subject_commit'],'HANDOFF subject mismatch')
    for field,key in [('contract_sha256','contract'),('input_manifest_sha256','input_manifest'),('evidence_manifest_sha256','evidence_manifest')]:
        need(result[field]==state[key]['sha256'],'HANDOFF '+field+' mismatch')
    final=state['stages'][-1]['attempts'][-1]
    need(result['review_sha256']==final['receipt']['sha256'],'HANDOFF reviewer binding mismatch')
    need(result['components']=={name:'PASS' for name in contract['components']},'component readiness incomplete')
    need(result['findings']=={name:'CLOSED' for name in contract['findings']},'finding closure incomplete')
    report=project.ref(result['report'],'HANDOFF report').decode('utf-8')
    need(state['subject_commit'] in report,'HANDOFF report subject missing')
    names(result['residual_risks'],'residual risks',False);names(result['owner_decisions'],'owner decisions',False)
    need(state['handoff_status'] in ('awaiting-architect','accepted'),'invalid handoff status')
    if state['handoff_status']=='awaiting-architect':
        need(state['external_review'] is None and state['architect_acceptance'] is None,'awaiting state cannot claim Architect response')
        return
    need(state['architect_acceptance'] is not None,'accepted state requires Architect response')
    need(state['external_review'] is not None,'accepted state requires external reporting review')
    response=project.ref(state['architect_acceptance'],'Architect response',True)
    review=project.ref(state['external_review'],'external reporting review',True)
    schema(response,'architect-acceptance','Architect response');schema(review,'architect-reporting-review','external reporting review')
    exact(response,('schema','kind','behavior_commit','reporting_commit','verdict','components','architect_task','reporting_review_sha256'),'Architect response')
    exact(review,('schema','kind','behavior_commit','reporting_commit','verdict','reviewer_task','handoff_sha256'),'external reporting review')
    need(response['behavior_commit']==review['behavior_commit']==state['subject_commit'],'accepted behavior mismatch')
    need(response['reporting_commit']==review['reporting_commit'],'accepted reporting subject mismatch')
    need(response['reporting_review_sha256']==state['external_review']['sha256'],'Architect external review binding mismatch')
    need(response['architect_task']==state['roles']['architect'] and review['reviewer_task']==state['roles']['reviewer'],'accepted task identity mismatch')
    need(response['verdict']==review['verdict']=='PASS' and response['components']==result['components'],'accepted component verdict incomplete')
    reporting=project.commit(review['reporting_commit'],'accepted reporting')
    head=project.head()
    need(project.ancestor(state['subject_commit'],reporting) and project.ancestor(reporting,head),'accepted reporting ancestry mismatch')
    stored=project.git('show',reporting+':'+state['_state_path'],check=False)
    need(stored.returncode==0,'accepted reporting STATE missing')
    old=load_json(stored.stdout,'accepted reporting STATE')
    need(isinstance(old,dict),'accepted reporting STATE must contain object')
    need(old.get('stage')=='handoff' and old.get('handoff_status')=='awaiting-architect','accepted reporting commit is not awaiting handoff')
    for key in ('subject_commit','contract','input_manifest','evidence_manifest','handoff'):
        need(old.get(key)==state[key],'accepted reporting packet mismatch: '+key)
    need(digest(project.blob(reporting,state['handoff']['path']))==review['handoff_sha256']==state['handoff']['sha256'],
        'accepted HANDOFF byte mismatch')
    try:
        validate_project(CommittedProject(project,reporting),state['_state_path'].rsplit('/',1)[0])
    except Invalid as error:
        raise Invalid('accepted reporting packet invalid: '+str(error))


STATE_KEYS=('schema','protocol','mode','stage','active_gate','subject_commit','subject_label','roles','contract',
    'input_manifest','evidence_manifest','stages','open_findings','handoff','handoff_status','external_review','architect_acceptance')


def attempt_history(project,state,contract,path):
    """Preserve declared attempts only within this frozen contract's ancestry.

    No reflogs/unrelated refs, receipt discovery or claim about unrecorded reviews.
    Reporting merges are explicitly unsupported rather than scanned first-parent.
    """
    subject=state['subject_commit'];head=project.head()
    revisions=project.git('rev-list','--reverse','--topo-order',subject+'..'+head).stdout.decode().splitlines()
    merges=project.git('rev-list','--min-parents=2',subject+'..'+head).stdout.decode().splitlines()
    need(not merges,'attempt history: reporting merges unsupported')
    current={record['id']:record['attempts'] for record in state['stages']}
    declared=False
    for revision in [subject]+revisions:
        raw=project.git('show',revision+':'+path,check=False)
        if raw.returncode:
            # Missing STATE before initial creation is normal; distinguish it
            # from an unreadable object in a resolved commit.
            names_at=project.blobs(revision)
            need(path not in names_at,'attempt history: STATE unreadable')
            need(not declared,'attempt history preservation: STATE disappeared after declaration')
            continue
        try:
            old=load_json(raw.stdout,'historical STATE')
            need(isinstance(old,dict),'STATE must contain object')
            if old.get('contract')!=state['contract']:continue
            declared=True
            need(type(old.get('schema')) is int and old['schema']==2,'same-contract STATE requires schema 2')
            exact(old,STATE_KEYS,'same-contract STATE')
            need(old.get('protocol')=='architect-protocol','protocol differs')
            project.commit(old['subject_commit'],'historical STATE subject')
            need(old['stage'] in LIFECYCLE and old['mode']=='production','historical lifecycle invalid')
            records=old.get('stages');need(isinstance(records,list),'stages must be list')
            need([r.get('id') if isinstance(r,dict) else None for r in records]==contract['stages'],'stage scope differs')
            for record in records:
                exact(record,('id','attempts','effective'),'historical stage')
                old_attempts=record['attempts'];need(isinstance(old_attempts,list),'attempts must be list')
                identifiers=[]
                for index,attempt in enumerate(old_attempts):
                    exact(attempt,('id','subject_commit','verdict','receipt','supersedes','bindings'),'historical attempt')
                    identifiers.append(text(attempt['id'],'historical attempt id'))
                    project.commit(attempt['subject_commit'],'historical attempt subject')
                    need(attempt['verdict'] in VERDICTS,'historical verdict invalid')
                    need(attempt['supersedes']==(identifiers[index-1] if index else None),'historical supersession differs')
                    if attempt['verdict']=='PENDING':
                        need(attempt['receipt'] is None,'historical pending attempt cannot claim receipt')
                    else:
                        exact(attempt['receipt'],('path','sha256'),'historical receipt reference')
                        path_parts(attempt['receipt']['path']);sha(attempt['receipt']['sha256'],'historical receipt digest')
                    if attempt['bindings'] is not None:
                        exact(attempt['bindings'],('contract','input_manifest','evidence_manifest'),'historical attempt bindings')
                        for key,ref in attempt['bindings'].items():
                            exact(ref,('path','sha256'),'historical '+key+' reference')
                            path_parts(ref['path']);sha(ref['sha256'],'historical '+key+' digest')
                need(len(identifiers)==len(set(identifiers)),'historical identity reused')
                now=current[record['id']]
                need([a['id'] for a in now[:len(identifiers)]]==identifiers,'declared attempt removed or reordered: '+record['id'])
                for old_attempt,new_attempt in zip(old_attempts,now):
                    if old_attempt['verdict']!='PENDING':
                        need(old_attempt==new_attempt,'completed attempt changed: '+record['id']+'/'+old_attempt['id'])
        except Invalid as error:
            raise Invalid('attempt history preservation: '+str(error))


def validate_project(project,packet_dir,example=False):
    prefix=packet_dir+'/'
    for name in ('PLAN.md','STAGES.md','ACCEPTANCE-MATRIX.md'):project.read(prefix+name)
    need(not project.has(prefix+'STATUS.md'),'competing STATUS.md in architect packet')
    state=load_json(project.read(prefix+'STATE.json'),'STATE.json')
    need(isinstance(state,dict),'STATE.json must contain object')
    need(type(state.get('schema')) is int and state['schema']==2,'STATE.json requires schema 2; migrate legacy packet')
    exact(state,STATE_KEYS,'STATE.json')
    need(state['protocol']=='architect-protocol','STATE.json protocol mismatch')
    need(state['stage'] in LIFECYCLE,'STATE.json stage invalid')
    need(state['mode'] in ('production','structural-example'),'STATE.json mode invalid')
    if state['mode']=='structural-example':
        need(example,'structural example requires explicit --structural-example')
        need(state['stage']=='scope' and state['subject_commit'] is None and state['active_gate'] is None,'structural example must be unfrozen scope')
    else:need(not example,'--structural-example cannot validate production packet')
    exact(state['roles'],('developer','reviewer','architect'),'roles')
    for value in state['roles'].values():text(value,'role task')
    need(len(set(state['roles'].values()))==3,'roles must be distinct tasks')
    text(state['subject_label'],'subject label');names(state['open_findings'],'open findings',False)
    for key in ('contract','input_manifest','evidence_manifest','handoff','external_review','architect_acceptance'):
        if state[key] is not None:
            label=key.replace('_',' ')
            exact(state[key],('path','sha256'),label+' reference')
            path_parts(state[key]['path']);sha(state[key]['sha256'],label+' digest')
    stage=state['stage'];subject=state['subject_commit']
    if stage=='scope':
        need(subject is None and state['active_gate'] is None and state['stages']==[],'scope must be unfrozen')
        need(all(state[key] is None for key in ('contract','input_manifest','evidence_manifest','handoff','handoff_status','external_review','architect_acceptance')),'scope cannot claim review artifacts')
        return ('STRUCTURAL architect: example only; no production acceptance' if example else 'PASS architect: scope; no reviewed behavior claim')
    project.commit(subject,'STATE.json immutable subject')
    contract=project.ref(state['contract'],'contract',True);contract_check(contract,state['contract'])
    need(set(state['open_findings'])<=set(contract['findings']),'finding scope differs')
    strict=stage in ('review','handoff')
    if strict or stage=='baseline':
        need(project.blob(subject,state['contract']['path'])==project.read(state['contract']['path']),'contract differs from frozen subject')
    evidence=None
    if strict:
        head=project.head()
        project.delta(subject,head,contract['reporting_paths'])
        inputs_check(project,subject,contract,state['input_manifest'])
        project.clean(head)
        evidence=evidence_check(project,state,contract)
    stages_check(project,state,contract,evidence)
    if stage=='handoff':
        need(not state['open_findings'],'in-scope findings remain open')
        state['_state_path']=prefix+'STATE.json'
        handoff_check(project,state,contract,evidence)
        attempt_history(project,state,contract,prefix+'STATE.json')
        return 'PASS architect: handoff / '+state['handoff_status']+'; packet bindings verified, not source truth or independent authority'
    need(state['handoff'] is None and state['handoff_status'] is None and state['external_review'] is None and state['architect_acceptance'] is None,
        'intermediate state cannot claim final handoff')
    if strict:attempt_history(project,state,contract,prefix+'STATE.json')
    return 'PASS architect: '+stage+'; current work is not accepted; historical scope requires accountable review'


class CommittedProject(Project):
    """Read an already reviewed reporting commit without creating a checkout.

    Every artifact, mode and nested binding comes from that immutable Git tree.
    There are no working/untracked files in this view, and no filesystem writes.
    """
    def __init__(self,project,revision):
        self.root=project.root
        self.revision=revision
        self.entries=self.blobs(revision)

    def head(self):return self.revision
    def mode(self,name):return self.entries[name]['mode']
    def has(self,name):return name in self.entries

    def read(self,name):
        path_parts(name)
        need(name in self.entries,name+' missing')
        return self.git('cat-file','blob',self.entries[name]['oid']).stdout

    def clean(self,head):
        need(head==self.revision,'immutable snapshot head mismatch')


def validate(root,packet_dir='docs/architect',example=False):
    project=Project(root);parts=path_parts(packet_dir)
    try:
        with project.directory(parts):pass
    except FileNotFoundError:return 'SKIP architect: packet absent'
    return validate_project(project,packet_dir,example)
