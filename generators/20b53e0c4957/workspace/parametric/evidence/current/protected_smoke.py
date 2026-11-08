from pathlib import Path
import importlib.util, json, sys
ROOT=Path(__file__).resolve().parents[6]
HERE=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]
from arcpuzzles.parametric_worker import _grid,_real_evaluator
spec=importlib.util.spec_from_file_location('f20',HERE/'family.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
rows=[]
try:
  for seed in (0,17):
    for policy in f.POLICIES:
      s={'hole_policy':policy}; ep=f.generate(seed,s,2,4)
      for split in ('train','test'):
        for i,pair in enumerate(ep[split]):
          actual=_grid(apply(ep['program_solution'],pair['input']))
          if actual!=pair['output']:
            raise AssertionError((seed,policy,split,i,actual,pair['output']))
          rows.append({'seed':seed,'settings':s,'split':split,'index':i})
finally:
  bridge.close()
out={'schema':'20b53e0c4957-protected-smoke-v1','status':'passed','racket':identity,'evaluations':len(rows),'cases':rows,'training_admitted':False}
path=HERE/'evidence/current/protected-smoke.json';path.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'passed','evaluations':len(rows),'out':str(path)}))
