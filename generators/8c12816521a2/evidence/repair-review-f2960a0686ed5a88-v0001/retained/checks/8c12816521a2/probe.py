"""Bounded one-rival learnability witness; labels come from protected Racket."""
from pathlib import Path
import hashlib, json, sys
ROOT=Path.cwd().resolve()
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]
from reviewer_support import load_selected_generator, canonical_pairs
from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
TASK='8c12816521a2'
PIN='5fd1dee61a1834b2f949ee08fe810fc5d9ce4207f1ae6200d1eac22e23d393ec'
OUT=ROOT.parent/'checks'/TASK
COMMAND='WORK/.venv/bin/python review.py run python3 ../checks/8c12816521a2/probe.py'
def hash_bytes(v): return hashlib.sha256(v).hexdigest()
def digest(v): return hash_bytes(json.dumps(v,sort_keys=True,separators=(',',':')).encode())
m,source,source_sha=load_selected_generator(TASK,root=ROOT)
assert source_sha==PIN,(source_sha,PIN)
variants=Catalog(ROOT)._variants()[TASK]
assert len(variants)==1
canonical=variants[0]['program_solution']
assert canonical.count('(yl (> ly ry))')==1
rival=canonical.replace('(yl (> ly ry))','(yl #t)')
programs={'canonical':canonical,'rival_fixed_left_after_transpose':rival}
for name,program in programs.items(): (OUT/(name+'.rkt')).write_text(program+'\n')
public=canonical_pairs(TASK,root=ROOT,variant=0)
scenarios=[{'name':'canonical_visible_demonstrations_and_query','pairs':public}]
search=[]
for seed in range(16):
 grids=[m.generate(seed,i) for i in range(3)]
 facts=[m._strict_facts(g)[1] for g in grids]
 sides=[f['yellow_left'] for f in facts]
 search.append({'seed':seed,'normalized_yellow_left':sides})
 if sides==[True,True,False]:
  scenarios.append({'name':'generated_default_profile_episode','seed':seed,'difficulty':None,'overrides':{},
   'pairs':[{'input':g,'split':'train' if i<2 else 'test','sample_index':i,
              'self_check':m.self_check(g),'scene_profile':m.observe_overrides(g)['scene_profile'],
              'facts':facts[i]} for i,g in enumerate(grids)]})
  break
apply,identity,bridge=_real_evaluator((ROOT/'shared/runtime').resolve())
try:
 for scenario in scenarios:
  for pair in scenario['pairs']:
   inp=pair['input']
   pair['input_sha256']=digest(inp)
   pair['canonical_output']=apply(canonical,inp)
   pair['rival_output']=apply(rival,inp)
   pair['canonical_output_sha256']=digest(pair['canonical_output'])
   pair['rival_output_sha256']=digest(pair['rival_output'])
   pair['equal']=pair['canonical_output']==pair['rival_output']
   pair['disagreement_cells']=[{'row':r,'col':c,'canonical':a,'rival':b}
      for r,(ra,rb) in enumerate(zip(pair['canonical_output'],pair['rival_output']))
      for c,(a,b) in enumerate(zip(ra,rb)) if a!=b]
   if 'output' in pair:
    pair['stored_label_verified']=pair['canonical_output']==pair['output']
    assert pair['stored_label_verified']
  scenario['all_demos_agree']=all(p['equal'] for p in scenario['pairs'] if p['split']=='train')
  scenario['query_disagrees']=any(not p['equal'] for p in scenario['pairs'] if p['split']=='test')
  assert scenario['all_demos_agree'] and scenario['query_disagrees']
finally: bridge.close()
receipt={'schema':'bounded-peer-learnability-witness-v1','task_id':TASK,
 'source_path':str(source.relative_to(ROOT)),'source_sha256':source_sha,
 'actual_command':COMMAND,'payload_cwd':str(ROOT),'protected_runtime':identity,
 'rival_description':'Always process yellow on the normalized left/above side; reverse-side yellow leaves its lane unchanged.',
 'program_sha256':{k:hash_bytes(v.encode()) for k,v in programs.items()},
 'program_file_sha256':{k:hash_bytes((OUT/(k+'.rkt')).read_bytes()) for k in programs},
 'probe_sha256':hash_bytes(Path(__file__).read_bytes()),
 'bounded_search':search,'scenarios':scenarios,
 'limits':['One deliberately simple fixed-direction rival; not an exhaustive rival search.',
  'This is finite-demonstration ambiguity, not evidence of incorrect canonical labels or a universal learning impossibility.',
  'At most 16 default-profile generator seeds and one native replay per retained input/program.',
  'No production source changes, no battery or native parametric acceptance claim.',
  'evidence/review_index.json absent; supplementary-current.json referenced manifest absent in packet.']}
(OUT/'witness.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'source_sha256':source_sha,'protected_runtime':identity,'program_sha256':receipt['program_sha256'],
 'seeds_probed':len(search),'scenarios':[{'name':s['name'],'seed':s.get('seed'),
 'demo_count':sum(p['split']=='train' for p in s['pairs']),
 'all_demos_agree':s['all_demos_agree'],'query_disagrees':s['query_disagrees'],
 'query_disagreement_cells':[len(p['disagreement_cells']) for p in s['pairs'] if p['split']=='test']}
 for s in scenarios]},indent=2))
