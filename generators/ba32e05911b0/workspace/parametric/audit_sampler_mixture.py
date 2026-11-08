"""Protected checks of seed-only sampler mixing and endpoint contracts."""
from pathlib import Path
from copy import deepcopy
import importlib.util,json,sys
HOME=Path(__file__).resolve().parent;ROOT=HOME.parents[3]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
from reviewer_support import public_challenge_bytes
spec=importlib.util.spec_from_file_location('_ba32_audited_mixture',HOME/'adapter.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
settings=[{'direction':d} for d in ('right','left')]
programs={s['direction']:A.program(s) for s in settings}
for s in settings:assert A.program(s)==A.INTERACTING.program(s)==A.SIX_ROLL.program(s)
rows=[];failures=[];evaluations=0
with _local_imports(ROOT/'shared/runtime',HOME):
 apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
 try:
  for seed in (0,17):
   baselines={s['direction']:A.generate(seed,s,6,4) for s in settings}
   for split in ('train','test'):
    assert [p['input'] for p in baselines['right'][split]]==[p['input'] for p in baselines['left'][split]]
   for demos,queries in ((2,1),(2,4),(6,1),(6,4)):
    for setting in settings:
     chosen=setting['direction'];episode=A.generate(seed,setting,demos,queries);pairs=episode['train']+episode['test'];actual={}
     assert episode['train']==baselines[chosen]['train'][:demos]
     assert episode['test']==baselines[chosen]['test'][:queries]
     if A.branch(seed)=='six_roll':original=A.SIX_ROLL.generate(seed,setting,demos,4)
     else:original=A.INTERACTING.generate(seed,setting,demos,queries)
     assert episode['train']==original['train'] and episode['test']==original['test'][:queries]
     for name,p in programs.items():
      actual[name]=[_grid(apply(p,pair['input'])) for pair in pairs];evaluations+=len(pairs)
     assert all(actual[chosen][i]==pair['output'] for i,pair in enumerate(pairs))
     survivors=[name for name in programs if all(actual[name][i]==pair['output'] for i,pair in enumerate(episode['train']))]
     row={'seed':seed,'branch':A.branch(seed),'demos':demos,'queries':queries,'setting':setting,'survivors':survivors}
     if survivors!=[chosen]:failures.append(row)
     first=A.public_turn(episode,0);one=A.generate(seed,setting,demos,1)
     assert first==A.public_turn(one,0)
     hidden=deepcopy(episode);hidden.update(settings={'private':1},seed=99,program_solution='private',branch='private')
     for pair in hidden['test']:pair['output']=[[9]]
     for pair in hidden['test'][1:]:pair['input']=[[9]]
     assert public_challenge_bytes(first)==public_challenge_bytes(A.public_turn(hidden,0))
     rows.append(row)
 finally:bridge.close()
report={'schema':'arcpuzzles-ba32-sampler-mixture-audit-v1','status':'passed' if not failures else 'failed','racket':identity,'evaluations':evaluations,'episodes':rows,'failures':failures,'program_bytes_unchanged':True,'sampler_source_outputs_preserved':True,'direction_matched_inputs':True,'independent_count_prefixes':True,'single_turn_privacy':True,'scope':'Both original teaching guards remain active; both programs execute on both curricula atseeds0/17 and2/6demo1/4query endpoints. Finite sampled evidence, not universal uniqueness.'}
out=HOME/'evidence/sampler-mixture-current';out.mkdir(parents=True,exist_ok=False);(out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':report['status'],'evaluations':evaluations,'failures':failures}))
raise SystemExit(0 if not failures else 1)
