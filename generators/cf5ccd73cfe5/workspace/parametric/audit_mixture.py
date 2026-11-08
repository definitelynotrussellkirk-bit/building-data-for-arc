"""Cross-curriculum program and full shortcut-bank check."""
from pathlib import Path
from copy import deepcopy
import importlib.util,json,sys
HOME=Path(__file__).resolve().parent;ROOT=HOME.parents[3]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
from reviewer_support import public_challenge_bytes
s=importlib.util.spec_from_file_location('_cf5_audited_mixture',HOME/'adapter.py');A=importlib.util.module_from_spec(s);s.loader.exec_module(A)
settings=[{'orientation':v} for v in A._prototype.SETTINGS];programs={s['orientation']:A.program(s) for s in settings}
for s in settings:assert A.program(s)==A.SUPPLEMENTAL.program(s)==A.ORIGINAL.program(s)
rows=[];failures=[];evaluations=0;reference={}
with _local_imports(ROOT/'shared/runtime',HOME):
 apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
 try:
  for seed in (0,17):
   for setting in settings:
    mode=setting['orientation'];e=A.generate(seed,setting,2,4);pairs=e['train']+e['test'];pred={}
    for n,p in programs.items():pred[n]=[_grid(apply(p,x['input'])) for x in pairs];evaluations+=len(pairs)
    assert all(pred[mode][i]==x['output'] for i,x in enumerate(pairs))
    surv=[n for n in programs if pred[n][:2]==[x['output'] for x in e['train']]]
    dp=[A._prototype.shortcut_outputs(x['input']) for x in e['train']]
    fits=[n for n in dp[0] if all(dp[i][n]==x['output'] for i,x in enumerate(e['train']))]
    harmful=[n for n in fits if any(A._prototype.shortcut_outputs(x['input'])[n]!=x['output'] for x in e['test'])]
    row={'seed':seed,'branch':A.branch(seed),'setting':setting,'survivors':surv,'full_shortcut_bank_survivors':fits,'harmful_survivors':harmful,'query_shapes':[[len(x['input']),len(x['input'][0])] for x in e['test']]}
    if surv!=[mode] or fits:failures.append(row)
    keys={split:[x['input'] for x in e[split]] for split in ('train','test')}
    if seed in reference:assert keys==reference[seed]
    reference[seed]=keys
    one=A.generate(seed,setting,2,1);assert one['train']==e['train'] and one['test']==e['test'][:1]
    visible={'train':e['train'],'test':e['test'][:1]};private=deepcopy(visible);private.update(seed=99,settings={'private':1},program='private');private['test'][0]['output']=[[9]]
    assert public_challenge_bytes(private)==public_challenge_bytes(visible)
    rows.append(row)
 finally:bridge.close()
r={'schema':'arcpuzzles-cf5-sampler-mixture-audit-v1','status':'passed' if not failures else 'failed','racket':identity,'evaluations':evaluations,'episodes':rows,'failures':failures,'all4program_texts_exact':True,'full_shortcut_bank':'8shortcuts×4orientations perselectedrule','matched_inputs_and_single_query_prefixes':True,'scope':'Seeds0/17coverbothcurricula,2demos4queries. All4programs executed. Full current Python shortcut bank checked against realRacket gold. Finite sampled evidence only.'}
out=HOME/'evidence/mixture-current';out.mkdir(parents=True,exist_ok=False);(out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print(json.dumps({'status':r['status'],'evaluations':evaluations,'failures':failures}))
raise SystemExit(0 if not failures else 1)
