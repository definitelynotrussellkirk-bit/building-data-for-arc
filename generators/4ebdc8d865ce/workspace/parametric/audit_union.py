"""Small protected three-program audit and source-bank teaching checks."""
from pathlib import Path
from copy import deepcopy
import importlib.util,json,sys,hashlib
HOME=Path(__file__).resolve().parent;ROOT=HOME.parents[3]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
s=importlib.util.spec_from_file_location('_4eb_union_audit',HOME/'adapter.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
s=importlib.util.spec_from_file_location('_4eb_anchor_rivals',HOME/'anchor/rivals.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
P=A.DEGREE._PROTOTYPE
programs={s['target_degree']:A.program(s) for s in A.SETTINGS}
expected={0:'99472c9502d886c3ad84ce6b2090f691cceb446ba067032ed54f62ffdaa4d271',1:'639dd3664d0b34c2e901fe8ee81d5d41e0bd24d6e97d8ed5d84f9a193f3c4021'}
for v,w in expected.items():assert hashlib.sha256(programs[v].encode()).hexdigest()==w
assert programs[0]==A.ANCHOR.program({'selection':'isolated_twos'})
def degree_rival(g,name):
 mask=[[2 if v==2 else 0 for v in row] for row in g]
 out=P._candidate_transform(mask,name)
 return [[out[r][c] if v==2 else v for c,v in enumerate(row)] for r,row in enumerate(g)]
rows=[];failures=[];evaluations=0;witnesses=[]
with _local_imports(ROOT/'shared/runtime',HOME):
 apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
 try:
  for seed in (0,17):
   for demos in (2,6):
    inputs=A.sample_inputs(seed,demos,4);grids=inputs['train']+inputs['test']
    assert len({json.dumps(g) for g in grids})==len(grids)
    actual={name:[_grid(apply(p,g)) for g in grids] for name,p in programs.items()};evaluations+=len(grids)*3
    for mode,values in actual.items():
     survivors=[name for name,pred in actual.items() if pred[:demos]==values[:demos]]
     if survivors!=[mode]:failures.append({'seed':seed,'demos':demos,'mode':mode,'kind':'declared','survivors':survivors})
     fits=[];harmful=[]
     for name in P.CANDIDATE_NAMES:
      if name=='target_degree_'+str(mode):continue
      dp=[degree_rival(g,name) for g in inputs['train']]
      if dp==values[:demos]:
       fits.append('old/'+name)
       if any(degree_rival(g,name)!=want for g,want in zip(inputs['test'],values[demos:])):harmful.append('old/'+name)
     for name in R.RIVAL_NAMES:
      if mode==0 and name=='isolated_twos' or mode=='anchor_area' and name=='anchor_sized_twos':continue
      dp=[R.predict(g,name) for g in inputs['train']]
      if dp==values[:demos]:
       fits.append('incoming/'+name)
       if any(R.predict(g,name)!=want for g,want in zip(inputs['test'],values[demos:])):harmful.append('incoming/'+name)
     row={'seed':seed,'demos':demos,'queries':4,'mode':mode,'survivors':survivors,'extra_demo_survivors':fits,'harmful':harmful,'anchor_sizes':[A.ANCHOR.analyze(g)['anchor_size'] for g in inputs['train']]}
     if fits:failures.append({'kind':'extra_rival_demo_survivor',**row})
     rows.append(row)
   grid=A.sample_inputs(seed,2,4)['train'][1]
   source=programs['anchor_area'];needle='(anchor-size (obj-size anchor))';replacement='(anchor-size (* (+ 1 (- (obj-r2 anchor) (obj-r1 anchor))) (+ 1 (- (obj-c2 anchor) (obj-c1 anchor)))))'
   assert source.count(needle)==1;counter=source.replace(needle,replacement)
   one=_grid(apply(source,grid));two=_grid(apply(counter,grid));evaluations+=2
   if one!=two:witnesses.append({'input':grid,'settings':{'target_degree':'anchor_area'},'program':source,'output':one,'counterfactual_program':counter,'counterfactual_output':two,'ablation':'occupied_area_to_bbox_area','intermediate':{'occupied_area':A.ANCHOR.analyze(grid)['anchor_size'],'bbox_area':A.ANCHOR.analyze(grid)['anchor_bbox_area']}})
 finally:bridge.close()
r={'schema':'arcpuzzles-4eb-union-audit-v1','status':'passed' if not failures else 'failed','racket':identity,'evaluations':evaluations,'episodes':rows,'failures':failures,'causal_cases':witnesses,'program_hashes':{str(k):hashlib.sha256(v.encode()).hexdigest() for k,v in programs.items()},'scope':'Seeds0/17,2/6demos,4queries; all3exactRacketprograms. Old16rivals on color2projection with allothercolors restored; incoming17rivals. Rival predictions are Python diagnostics against realRacket gold. Demo-fit computed without query labels; query comparisons only severity diagnostics.'}
out=HOME/'evidence/union-final';out.mkdir(parents=True,exist_ok=False);(out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':r['status'],'evaluations':evaluations,'failures':failures,'causal_cases':len(witnesses)}))
raise SystemExit(0 if not failures else 1)
