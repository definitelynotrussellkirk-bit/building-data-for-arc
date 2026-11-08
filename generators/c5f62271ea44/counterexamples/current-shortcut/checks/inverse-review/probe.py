import json,sys,hashlib,importlib.util,collections
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parent.parent/'repo'
sys.path.insert(0,str(root/'shared/runtime'));sys.path.insert(0,str(root/'generators/c5f62271ea44/workspace/parametric'))
from direction import RuleExecutor
from reviewer_support import canonical_pairs
source=here/'generator_v3_2_0_interim.py';sh=hashlib.sha256(source.read_bytes()).hexdigest();assert sh=='8e242979e5d7db509e8298c877fa99c8a8143505c7fb2ff74e32a0c25924aa82'
spec=importlib.util.spec_from_file_location('g',source);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
quarters={'rot_cw','rot_ccw'};firsts={};counts=collections.Counter()
for seed in range(128):
 order=[g.schedule_profile(seed,i) for i in range(8)]
 for start in range(8):
  syms=[order[(start+j)%8] for j in range(5)];counts['windows']+=1
  if sum(s in quarters for s in syms)==1:
   qi=next(i for i,s in enumerate(syms) if s in quarters);rec=dict(seed=seed,start=start,query_position=qi,query_sample_index=start+qi,syms=syms)
   firsts.setdefault('rotation',rec);counts['ambiguous_rotations']+=1
   if qi==4:firsts.setdefault('production',rec);counts['ambiguous_production']+=1
report=dict(source_sha256=sh,version=g.VERSION,analytical_schedule_counts=counts,analytical_scope='128 seeds x8 starts, five-pair windows; not Racket call counts',witnesses={},canonical=[])
with RuleExecutor(root) as ex:
 report['rules']={k:dict(text_sha256=hashlib.sha256(s.encode()).hexdigest(),normalized_rule_hash=hashlib.sha256(' '.join(s.split()).encode()).hexdigest()[:12]) for k,s in ex.sources.items()}
 for k,s in ex.sources.items():(here/f'{k}.rkt').write_text(s)
 for pair in canonical_pairs(g.TASK_ID,root=root):
  forward=ex.apply(pair['input'],'forward');inverse=ex.apply(pair['input'],'inverse')
  report['canonical'].append(dict(input_sha256=hashlib.sha256(json.dumps(pair['input'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),forward_matches_label=forward==pair['output'],inverse_matches_label=inverse==pair['output']))
 for kind,rec in firsts.items():
  pairs=[]
  for j in range(5):
   grid=g.generate(rec['seed'],rec['start']+j,difficulty='medium')
   forward=ex.apply(grid,'forward');inverse=ex.apply(grid,'inverse')
   pairs.append(dict(sample_index=rec['start']+j,input=grid,output=forward,inverse_output=inverse,input_sha256=hashlib.sha256(json.dumps(grid,sort_keys=True,separators=(',',':')).encode()).hexdigest(),symmetry=rec['syms'][j]))
  qi=rec['query_position'];di=[j for j in range(5) if j!=qi];demos=[dict(input=pairs[j]['input'],output=pairs[j]['output']) for j in di];query=dict(input=pairs[qi]['input'],output=pairs[qi]['output'])
  report['witnesses'][kind]=dict(**rec,difficulty='medium',demo_positions=di,pairs=pairs,old_hook_errors=g.lesson_identifiable(demos,query),inverse_fits_all_demos=all(pairs[j]['output']==pairs[j]['inverse_output'] for j in di),inverse_disagrees_query=pairs[qi]['output']!=pairs[qi]['inverse_output'])
 report['actual_racket_calls']=ex.calls
report['executor_source_sha256']=hashlib.sha256((root/'generators/c5f62271ea44/workspace/parametric/direction.py').read_bytes()).hexdigest()
(here/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['witnesses','canonical']},indent=2))
print('canonical',len(report['canonical']), 'forward fits',sum(x['forward_matches_label'] for x in report['canonical']), 'inverse fits',sum(x['inverse_matches_label'] for x in report['canonical']))
for kind,w in report['witnesses'].items():print(kind,{k:v for k,v in w.items() if k!='pairs'})
