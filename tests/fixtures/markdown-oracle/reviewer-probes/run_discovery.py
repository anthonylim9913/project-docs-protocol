import json, subprocess, sys, tempfile, importlib.util, shutil, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[4];sys.path.insert(0,str(root/'scripts'))
import register_paths
spec=importlib.util.spec_from_file_location('migration_review',root/'scripts/docs-migrate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
block=(root/'SKILL.md').read_text().split('### Step 2',1)[1].split('```markdown',1)[1].split('```',1)[0].strip('\n')+'\n'
TODAY='2026-09-11'
def seed(p,complete=True):
 p.mkdir(parents=True,exist_ok=True)
 for name,body in {'STATUS.md':'# STATUS\n\nLast updated: 2026-09-11\n\n## In flight\n\n- Ship reviewed repair\n','CHANGELOG.md':'# CHANGELOG\n\n## 2026-09-11 — initialized project documentation system\n\nInstalled.\n','README.md':'*Installed via the `project-docs-protocol` skill.*\n'}.items():(p/name).write_text(body)
 if complete:(p/'DECISIONS.md').write_text('# DECISIONS\n')
def snap(p):return {str(x.relative_to(p)):x.read_bytes() for x in p.rglob('*') if x.is_file()}
def cli(tool,p,*args):return subprocess.run([sys.executable,'-B',str(root/f'scripts/docs-{tool}.py'),str(p),'--today',TODAY,*args],text=True,capture_output=True,timeout=15)
def approved(plan):
 for item in plan['mappings']:
  if not item['existing']:item['reviewed']=True;item['row']['closes_when']='Independent review checks pass.'
 return plan
observations=[]
with tempfile.TemporaryDirectory(prefix='independent-discovery-') as tmp:
 base=Path(tmp).resolve()
 cases=[('root-only',True,None,'.',()),('docs-only',None,True,'docs',()),('root-empty-docs',True,'empty','.',()),('complete-root-two-file-docs',True,False,'.',()),('partial-root-complete-docs',False,True,'docs',()),('two-complete-root-explicit',True,True,'.',('--register-dir','.')),('two-complete-docs-explicit',True,True,'docs',('--register-dir','docs')),('custom-explicit',None,None,'records',('--register-dir','records'))]
 for name,root_state,docs_state,selected,args in cases:
  p=base/name;p.mkdir()
  if root_state is not None:seed(p,root_state)
  if docs_state=='empty':(p/'docs').mkdir()
  elif docs_state is not None:seed(p/'docs',docs_state)
  if selected=='records':seed(p/'records')
  (p/'AGENTS.md').write_text(block.replace('<docs-path>',selected))
  before=snap(p)
  result=cli('doctor',p,'--no-git',*args)
  assert result.returncode in (0,1), (name,result.stdout,result.stderr)
  assert 'PASS  wiring-path' in result.stdout,(name,result.stdout)
  assert before==snap(p)
  planfile=base/(name+'.json');preview=cli('migrate',p,'--plan',str(planfile),*args)
  assert preview.returncode==0,(name,preview.stderr)
  plan=json.loads(planfile.read_text());assert plan['register_dir']==str((p/selected).resolve())
  planfile.write_text(json.dumps(approved(plan)))
  apply=cli('migrate',p,'--write','--plan',str(planfile),*args)
  assert apply.returncode==0,(name,apply.stderr)
  after=snap(p);target=(p/selected).resolve()
  allowed={str((target/n).relative_to(p)) for n in ['CHANGELOG.md','LEDGER.md','LEDGER-ARCHIVE.md',m.JOURNAL]}
  changed={n for n in set(before)|set(after) if before.get(n)!=after.get(n)}
  assert changed<=allowed,(name,changed-allowed)
  assert (target/'LEDGER.md').is_file()
  observations.append({'case':name,'doctor_exit':result.returncode,'migration_preview_exit':preview.returncode,'migration_write_exit':apply.returncode,'only_selected_outputs_changed':True})
 p=base/'ambiguous';p.mkdir();seed(p);seed(p/'docs');before=snap(p)
 for tool,exit_code in [('doctor',3),('migrate',2)]:
  result=cli(tool,p);assert result.returncode==exit_code and '--register-dir' in result.stderr,(tool,result.stdout,result.stderr)
 assert snap(p)==before
 observations.append({'case':'two-complete-unselected','doctor_exit':3,'migration_exit':2,'unchanged':True})
 p=base/'preinstall';p.mkdir();seed(p/'docs',False);before=snap(p)
 for args in [(),('--register-dir','docs'),('--pre-install',)]:
  result=cli('migrate',p,*args);assert result.returncode==2,(args,result.stderr)
 assert snap(p)==before
 planfile=base/'preinstall.json';args=('--pre-install','--register-dir','docs','--plan',str(planfile))
 assert cli('migrate',p,*args).returncode==0
 planfile.write_text(json.dumps(approved(json.loads(planfile.read_text()))))
 result=cli('migrate',p,*args,'--write');assert result.returncode==0,result.stderr
 assert not (p/'docs/DECISIONS.md').exists()
 assert before['docs/STATUS.md']==(p/'docs/STATUS.md').read_bytes()
 observations.append({'case':'explicit-preinstall','rejected_missing_flag_or_path':True,'migration_write_exit':0,'status_preserved':True,'decisions_not_invented':True})
 p=base/'replay';p.mkdir();a=p/'alpha';b=p/'beta';seed(a);seed(b)
 plan=approved(m.build_plan(a,TODAY));planfile=base/'replay-plan.json';planfile.write_text(json.dumps(plan))
 real=m.atomic_write
 def interrupted(path,content):
  if path.name=='CHANGELOG.md':raise OSError('simulated interruption after durable prepared journal')
  return real(path,content)
 m.atomic_write=interrupted
 try:
  m.apply_plan(a,plan,TODAY)
  raise AssertionError('interruption not raised')
 except OSError as exc:assert 'simulated interruption' in str(exc)
 finally:m.atomic_write=real
 journal=json.loads((a/m.JOURNAL).read_text());assert journal['state']=='prepared'
 shutil.copyfile(a/m.JOURNAL,b/m.JOURNAL)
 before=snap(p)
 result=cli('migrate',p,'--register-dir','beta','--write','--plan',str(planfile))
 assert result.returncode==2 and 'register target differs' in result.stderr,result.stderr
 assert snap(p)==before
 resumed=cli('migrate',p,'--register-dir','alpha','--write','--plan',str(planfile));assert resumed.returncode==0,resumed.stderr
 after=snap(p);repeat=cli('migrate',p,'--register-dir','alpha','--write','--plan',str(planfile));assert repeat.returncode==0,repeat.stderr;assert after==snap(p)
 observations.append({'case':'target-binding-before-prepared-journal-replay','redirect_exit':2,'redirect_unchanged':True,'intended_resume_exit':0,'same_plan_repeat_unchanged':True})
print(json.dumps({'reviewed_hashes':{n:hashlib.sha256((root/'scripts'/n).read_bytes()).hexdigest() for n in ['docs-doctor.py','docs-migrate.py','register_paths.py']},'observations':observations},indent=2))
