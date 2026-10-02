import sys, re, json, hashlib, importlib.util
import importlib.metadata
from pathlib import Path
from markdown_it import MarkdownIt
root=Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root/'scripts'))
spec=importlib.util.spec_from_file_location('doctor_review',root/'scripts/docs-doctor.py'); d=importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
text=(root/'SKILL.md').read_text()
block=text.split('### Step 2',1)[1].split('```markdown',1)[1].split('```',1)[0].strip('\n').replace('<docs-path>','docs')+'\n'
needle='This project uses the project-docs-protocol'
assert importlib.metadata.version('markdown-it-py') == '4.0.0'
parser=MarkdownIt('commonmark')
def indent(block,n): return '\n'.join(' '*n+l if l.strip() else '' for l in block.splitlines())+'\n'
cases={}
for marker in ['-','+','*','1.','2.','10.','1)']:
 for gap in ['','\n']:
  for n in range(0,13):
   cases[f'single-{marker}-{bool(gap)}-{n}']=marker+' Outer\n'+gap+indent(block,n)
for a,b in [('-','-'),('-','1.'),('1.','-'),('1.','2.'),('10.','20.'),('*','+'),('1)','2)')]:
 for n in range(2,9):
  for gap in ['','\n']:
   for continuation in range(n+1,n+9):
    cases[f'nested-{a}-{b}-{n}-{bool(gap)}-{continuation}']=a+' Outer\n'+gap+' '*n+b+' Inner\n\n'+indent(block,continuation)
for marker in ['-','*','+','1.','10.']:
 for pad in range(1,9):
  for tight in [False,True]:
   lines=[l for l in block.splitlines() if l.strip()] if tight else block.splitlines()
   cases[f'marker-{marker}-{pad}-{tight}']=marker+' '*pad+lines[0]+'\n'+indent('\n'.join(lines[1:]),len(marker)+pad)
for prefix in ['Paragraph\n', '- Paragraph\n', '1. Paragraph\n', '- Outer\n    - Inner\n']:
 for n in range(0,13):
  cases[f'lazy-{prefix!r}-{n}']=prefix+indent('\n'.join(l for l in block.splitlines() if l.strip()),n)
mismatches=[]
observations=[]
for name,source in cases.items():
 tokens=parser.parse(source)
 oracle=any(t.type=='inline' and needle in t.content for t in tokens)
 visible=[l for _,l,_ in d.visible_lines(source.splitlines())]
 actual=any(needle in l for l in visible)
 observations.append({'name':name,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'oracle_live':oracle,'doctor_live':actual})
 if oracle!=actual:
  mismatches.append({'name':name,'oracle_live':oracle,'doctor_live':actual,'source':source,'visible':visible,'tokens':[{'type':t.type,'map':t.map,'content':t.content} for t in tokens if t.map]})
out=Path('/tmp/independent-doctor-oracle-results.json');out.write_text(json.dumps({'total':len(cases),'parser':'markdown-it-py 4.0.0; commonmark preset','doctor_script_sha256':hashlib.sha256((root/'scripts/docs-doctor.py').read_bytes()).hexdigest(),'install_block':block,'observations':observations,'mismatches':mismatches},indent=2))
print('cases:',len(cases),'visibility mismatches:',len(mismatches),'details:',out)
for m in mismatches[:35]: print(m['name'],m['oracle_live'],m['doctor_live'])
