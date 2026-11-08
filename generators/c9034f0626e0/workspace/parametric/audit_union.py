"""Bounded protected execution and finite-rival check for the four-rule union."""
from pathlib import Path
from copy import deepcopy
import importlib.util,json,sys
HOME=Path(__file__).resolve().parent;ROOT=HOME.parents[3]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
from reviewer_support import public_challenge_bytes
s=importlib.util.spec_from_file_location('_c903_audited_union',HOME/'adapter.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
programs={m:A.program({'lattice_rule':m}) for m in A.MODES}
assert programs['period2']==A.AREA.program({'spacing_rule':'period_2'})
assert programs['period3']==A.AREA.program({'spacing_rule':'period_3'})
rows=[];failures=[];evaluations=0
with _local_imports(ROOT/'shared/runtime',HOME):
 apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
 try:
  for seed in (0,17):
   for demos in (2,3,6):
    for mode in A.MODES:
     setting={'lattice_rule':mode};e=A.generate(seed,setting,demos,4);pairs=e['train']+e['test'];pred={}
     for name,p in programs.items():
      pred[name]=[_grid(apply(p,pair['input'])) for pair in pairs];evaluations+=len(pairs)
     assert all(pred[mode][i]==pair['output'] for i,pair in enumerate(pairs))
     survivors=[name for name in programs if all(pred[name][i]==pair['output'] for i,pair in enumerate(e['train']))]
     row={'seed':seed,'branch':('area' if mode=='ray_area_plus_one' else 'parity'),'demos':demos,'queries':4,'mode':mode,'survivors':survivors}
     if survivors!=[mode]:failures.append({'kind':'declared_underidentified',**row})
     rivals=(lambda g:A.AREA._module.rivals(g,'ray_component')) if mode=='ray_area_plus_one' else (lambda g:A.core.rivals.rival_predictions(g,mode))
     dp=[rivals(p['input']) for p in e['train']]
     fits=[n for n in dp[0] if all(dp[i][n]==p['output'] for i,p in enumerate(e['train']))]
     harmful=[n for n in fits if any(rivals(p['input'])[n]!=p['output'] for p in e['test'])]
     row['finite_rival_survivors']=fits;row['harmful_rivals']=harmful
     if harmful:failures.append({'kind':'finite_rival_underidentified',**row})
     one=A.generate(seed,setting,demos,1)
     assert e['train']==one['train'] and e['test'][:1]==one['test']
     first=A.public_challenge(e,query_index=0);changed=deepcopy(e)
     changed.update(seed=999,settings={'private':1},program_solution='private')
     for p in changed['test']:p['output']=[[9]]
     for p in changed['test'][1:]:p['input']=[[9]]
     assert public_challenge_bytes(first)==public_challenge_bytes(A.public_challenge(changed,query_index=0))
     assert first==A.public_challenge(one,query_index=0)
     rows.append(row)
 finally:bridge.close()
report={'schema':'arcpuzzles-c903-union-audit-v1','status':'passed' if not failures else 'failed','racket':identity,'evaluations':evaluations,'episodes':rows,'failures':failures,'all4programs_exact':True,'public_query_prefixes_private_invariant':True,'scope':'Bothcurricula atseeds0/17 with2/3/6demos and4queries; all4programs execute and selectedlabels match. Original finite Python rival banks screen demo-only fit/query disagreement; those predictions are diagnostic, not independent Racket proof. Old parity2demo count behavior retained.'}
out=HOME/'evidence/disjoint-union-current';out.mkdir(parents=True,exist_ok=False);(out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':report['status'],'evaluations':evaluations,'failures':failures}))
raise SystemExit(0 if not failures else 1)
