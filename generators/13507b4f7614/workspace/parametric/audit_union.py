"""Bounded direct protected-Racket check of the four-rule disjoint union."""
from pathlib import Path
from copy import deepcopy
import hashlib,importlib.util,json,sys

HOME=Path(__file__).resolve().parent
ROOT=HOME.parents[3]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
spec=importlib.util.spec_from_file_location('_13507_audited_union',HOME/'adapter.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
raw=lambda v:(json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
settings=[{'join_axis':v} for v in A.VALUES]
programs={s['join_axis']:A.program(s) for s in settings}
for s in settings[:3]:assert A.program(s)==A.JOIN.program(s)
assert A.program(settings[0])==A.CASCADE.canonical_source()
output=ROOT/'var/union-audit-current';output.mkdir(parents=True,exist_ok=False)
rows=[];failures=[];evaluations=0
with _local_imports(ROOT/'shared/runtime',HOME):
 apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
 try:
  for seed in (0,17):
   for demos in (2,6):
    for setting in settings:
     episode=A.generate(seed,setting,demos,4);actual={}
     pairs=episode['train']+episode['test']
     for name,p in programs.items():
      actual[name]=[_grid(apply(p,pair['input'])) for pair in pairs];evaluations+=len(pairs)
     chosen=setting['join_axis']
     assert all(actual[chosen][i]==pair['output'] for i,pair in enumerate(pairs))
     survivors=[name for name in programs if all(actual[name][i]==pair['output'] for i,pair in enumerate(episode['train']))]
     row={'seed':seed,'demos':demos,'queries':4,'setting':setting,'branch':A.branch(seed,setting),'survivors':survivors}
     if survivors != [chosen]:failures.append(row)
     if A.branch(seed,setting)=='cascade':
      expected=A.CASCADE.program({'selection_rule':'cross_area_cascade' if chosen=='cross_area_cascade' else 'all_odd'})
      authored=[_grid(apply(expected,pair['input'])) for pair in pairs];evaluations+=len(pairs)
      assert authored==actual[chosen]
     short=A.generate(seed,setting,2,1)
     assert short['train']==episode['train'][:2] and short['test']==episode['test'][:1]
     assert A.public_turn({'train':episode['train'],'test':short['test']})==A.public_turn(episode)
     hidden=deepcopy(episode)
     for p in hidden['test'][1:]:p['input']=[[9]]
     for p in hidden['test']:p['output']=[[9]]
     hidden.update(program_solution='secret',settings={'secret':1},seed=999)
     assert A.public_turn(hidden)==A.public_turn(episode)
     rows.append(row)
 finally:bridge.close()
report={'schema':'arcpuzzles-13507-union-audit-v1','status':'passed' if not failures else 'failed','racket':identity,'evaluations':evaluations,'episodes':rows,'failures':failures,'legacy_program_bytes_preserved':True,'cascade_matches_original_on_original_draws':True,'count_prefixes_and_single_turn_privacy':True,'scope':'All4programs execute on all sampled inputs; survivors fitdemonstrationsonly. Seeds0/17 at2/6demos and4queries. No universal uniqueness or acceptance.'}
(output/'report.json').write_bytes(raw(report));print(json.dumps({'status':report['status'],'evaluations':evaluations,'failures':failures}))
raise SystemExit(0 if not failures else 1)
