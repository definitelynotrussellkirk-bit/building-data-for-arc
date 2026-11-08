"""Bounded default-lesson adversarial probe; run with packet review.py run."""
import hashlib,json
from pathlib import Path
from reviewer_support import find_root,load_selected_generator
from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
ROOT=find_root(__file__); TASK='a41ff6269d40'; OUT=Path(__file__).resolve().parent
gen,source,source_sha=load_selected_generator(TASK,root=ROOT)
programs={v['program_solution'] for v in Catalog(ROOT).get(TASK)['variants']}
assert len(programs)==1
program=programs.pop()
def norm(cells):
 r0=min(r for r,c in cells);c0=min(c for r,c in cells)
 return sorted((r-r0,c-c0) for r,c in cells)
def transformed(shape,code):
 pts=list(shape)
 if code>=4:pts=[(r,-c) for r,c in pts]
 for _ in range(code%4):pts=[(c,-r) for r,c in pts]
 return norm(pts)
def solve(g,role=None,code=None,keep=False,keep_anchors=False):
 shape=norm([(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==4]);out=[[0]*len(g[0]) for _ in g]
 for r,row in enumerate(g):
  for c,v in enumerate(row):
   if (keep and v==4) or (keep_anchors and v in (1,2,3)):out[r][c]=v
   if v in (1,2,3):
    t=transformed(shape,code if v==role else {1:0,2:4,3:6}[v])
    for dr,dc in t:
     if 0<=r+dr<len(g) and 0<=c+dc<len(row):out[r+dr][c+dc]=4
 return out
rivals={f'role{role}_d4_{code}':(lambda g,role=role,code=code:solve(g,role,code)) for role in (1,2,3) for code in range(8) if code!={1:0,2:4,3:6}[role]}
rivals.update(retain_source=lambda g:solve(g,keep=True),retain_anchors=lambda g:solve(g,keep_anchors=True))
report={'task_id':TASK,'source_sha256':source_sha,'program':program,'program_sha256':hashlib.sha256(program.encode()).hexdigest(),'rival_names':list(rivals),'lessons':[],'limits':'Two default lessons, finite Python rival predictions checked against protected Racket authority labels. No broad battery or uniqueness proof.'}
with _local_imports(ROOT/'shared/runtime',source.parent):
 execute,identity,bridge=_real_evaluator(ROOT/'shared/runtime');report['racket']=identity
 try:
  for seed in (0,17):
   pairs=[]
   for index in range(4):
    g=gen.generate(seed,index);assert not gen.self_check(g);out=_grid(execute(program,g));assert solve(g)==out
    pairs.append({'input':g,'output':out})
   results=[]
   for name,rival in rivals.items():
    agreement=[rival(p['input'])==p['output'] for p in pairs[:3]]
    results.append({'name':name,'demo_agreement':agreement,'query_disagreement':rival(pairs[3]['input'])!=pairs[3]['output'] if all(agreement) else None})
   report['lessons'].append({'seed':seed,'difficulty':None,'sample_indices':[0,1,2,3],'train':pairs[:3],'test':pairs[3:],'rivals':results})
 finally:bridge.close()
report['findings']=[{'seed':l['seed'],**r} for l in report['lessons'] for r in l['rivals'] if r['query_disagreement']]
report['status']='finding' if report['findings'] else 'bounded_no_finding'
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_sha
(OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'source_sha256':source_sha,'protected_labels':8,'rivals':len(rivals),'findings':report['findings'],'demo_survivors':{l['seed']:[r['name'] for r in l['rivals'] if all(r['demo_agreement'])] for l in report['lessons']}},indent=2))
