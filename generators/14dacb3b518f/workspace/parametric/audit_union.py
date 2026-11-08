"""Execute every union program on both unchanged source curricula."""
from pathlib import Path
from copy import deepcopy
import hashlib,importlib.util,json,sys
HOME=Path(__file__).resolve().parent;ROOT=HOME.parents[3]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
from reviewer_support import public_challenge_bytes
spec=importlib.util.spec_from_file_location('_14dac_audited_union',HOME/'adapter.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
settings=[{'rule_mode':v} for v in A.VALUES]
programs={s['rule_mode']:A.program(s) for s in settings}
assert programs['hole_presence']==A.THRESHOLD.program({'min_holes':1})
for s in settings[:2]:assert A.program(s)==A.SIZE.program(s)
raw=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
rows=[];failures=[];evaluations=0
with _local_imports(ROOT/'shared/runtime',HOME):
 apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
 try:
  for seed in (0,17):
   for demos in (2,6):
    for setting in settings:
     chosen=setting['rule_mode'];episode=A.generate(seed,setting,demos,4);pairs=episode['train']+episode['test'];actual={}
     for name,program in programs.items():
      actual[name]=[_grid(apply(program,pair['input'])) for pair in pairs];evaluations+=len(pairs)
     assert all(actual[chosen][i]==pair['output'] for i,pair in enumerate(pairs))
     survivors=[name for name in programs if all(actual[name][i]==pair['output'] for i,pair in enumerate(episode['train']))]
     row={'seed':seed,'demos':demos,'queries':4,'setting':setting,'survivors':survivors}
     if survivors!=[chosen]:failures.append(row)
     if chosen=='min_holes_2':original=A.THRESHOLD.generate(seed,{'min_holes':2},demos,4)
     else:original=A.SIZE.generate(seed,setting,demos,4)
     assert original==episode
     short=A.generate(seed,setting,2,1)
     assert short['train']==episode['train'][:2] and short['test']==episode['test'][:1]
     first={'train':episode['train'],'test':episode['test'][:1]}
     changed=deepcopy(episode);changed.update(settings={'private':1},seed=999,program_solution='private')
     for pair in changed['test']:pair['output']=[[9]]
     for pair in changed['test'][1:]:pair['input']=[[9]]
     assert public_challenge_bytes(first)==public_challenge_bytes({'train':changed['train'],'test':changed['test'][:1]})
     assert public_challenge_bytes(first)==public_challenge_bytes({'train':episode['train'],'test':short['test']})
     rows.append(row)
 finally:bridge.close()
report={'schema':'arcpuzzles-14dac-union-audit-v1','status':'passed' if not failures else 'failed','racket':identity,'evaluations':evaluations,'episodes':rows,'failures':failures,'all3programs_byte_exact':True,'source_samplers_preserved':True,'prefix_and_single_turn_privacy':True,'scope':'All3programs on every sampled input; seeds0/17,2or6demos/4queries. Demo-only survivors required. No universal induction claim or acceptance.'}
output=HOME/'evidence/union-current';output.mkdir(parents=True,exist_ok=False);(output/'report.json').write_bytes(raw(report));print(json.dumps({'status':report['status'],'evaluations':evaluations,'failures':failures}))
raise SystemExit(0 if not failures else 1)
