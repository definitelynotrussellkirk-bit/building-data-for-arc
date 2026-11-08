"""Small protected audit of shared teaching, query-bank mixture and three rules."""
from pathlib import Path
from copy import deepcopy
import importlib.util,json,sys
HOME=Path(__file__).resolve().parent;ROOT=HOME.parents[3]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
s=importlib.util.spec_from_file_location('_b98_audited_union',HOME/'adapter.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
s=importlib.util.spec_from_file_location('_b98_old_rivals',HOME/'self_audit.py');OLD=importlib.util.module_from_spec(s);s.loader.exec_module(OLD)
programs={v:A.program({'bottom_order':v}) for v in A.VALUES};assert programs['left_right']==A.FEWEST.canonical_program()
for v in A.VALUES[:2]:assert programs[v]==A.COLOR.program({'bottom_order':v})
rows=[];failures=[];evaluations=0;witnesses=[]
with _local_imports(ROOT/'shared/runtime',HOME):
 apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
 try:
  for seed in (0,17):
   original=A._inputs(seed)
   for demos in (2,6):
    ins={split:original[split][:count] for split,count in (('train',demos),('test',4))};grids=ins['train']+ins['test']
    actual={name:[_grid(apply(p,g)) for g in grids] for name,p in programs.items()};evaluations+=len(grids)*3
    for name in programs:
     selected=actual[name];surv=[n for n,v in actual.items() if v[:demos]==selected[:demos]]
     if surv!=[name]:failures.append({'seed':seed,'demos':demos,'mode':name,'kind':'declared','survivors':surv})
     rival_rows=[]
     # Both authored rival banks are fitted to common demos without query hints.
     for rival,p in OLD.rival_programs().items():
      values=[_grid(apply(p,g)) for g in grids];evaluations+=len(grids)
      if values[:demos]==selected[:demos] and values[demos:]!=selected[demos:]:failures.append({'seed':seed,'demos':demos,'mode':name,'rival':rival,'kind':'old_rival'})
     pred=[A.FEWEST._rival_outputs(g) for g in grids]
     for rival in pred[0]:
      fits=all(pred[i][rival]==selected[i] for i in range(demos));diff=any(pred[i][rival]!=selected[i] for i in range(demos,len(grids)))
      if fits and diff:failures.append({'seed':seed,'demos':demos,'mode':name,'rival':rival,'kind':'incoming_rival'})
     rows.append({'seed':seed,'demos':demos,'queries':4,'mode':name,'survivors':surv,'query_bank':'old' if seed%2==0 else 'incoming'})
   if seed==17:
    grid=original['test'][3];counter=(HOME/'fewest/fewest_cells_canvas_midpoint.rkt').read_text();one=_grid(apply(programs['fewest_cells_first'],grid));two=_grid(apply(counter,grid));evaluations+=2;assert one!=two
    witnesses.append({'input':grid,'program':programs['fewest_cells_first'],'output':one,'counterfactual_program':counter,'counterfactual_output':two,'ablation':'wrong_midpoint','intermediate':A.FEWEST.dependency_intermediate(grid,'fewest_cells_first')})
 finally:bridge.close()
r={'schema':'arcpuzzles-b98-union-audit-v1','status':'passed' if not failures else 'failed','racket':identity,'evaluations':evaluations,'episodes':rows,'failures':failures,'causal_cases':witnesses,'scope':'Seeds0/17,2/6demos,4queries; all3exactprograms and old3rivals execute. Incoming6Pythonrivals diagnostic. Shared query-blind teaching and rule-independent query-bank draws. Finite evidence only.'}
out=HOME/'evidence/union-current';out.mkdir(parents=True,exist_ok=False);(out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':r['status'],'evaluations':evaluations,'failures':failures}))
raise SystemExit(0 if not failures else 1)
