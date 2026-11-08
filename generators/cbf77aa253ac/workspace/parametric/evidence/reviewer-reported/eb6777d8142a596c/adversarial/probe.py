from pathlib import Path
import sys, importlib.util, json, time, hashlib, tempfile
from copy import deepcopy
sys.path.insert(0,str(Path('shared/runtime').resolve()))
t=time.monotonic()
source=Path('generators/cbf77aa253ac/workspace/parametric/prototype.py')
spec=importlib.util.spec_from_file_location('adversarial_proto',source); p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
results={'command':'python3 review.py run python3 ../checks/adversarial/probe.py','findings':[], 'checks':{}}
results['source_hashes']={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [source,Path('generators/cbf77aa253ac/tests/test_parametric_cbf77aa253ac.py'),Path('generators/cbf77aa253ac/tests/test_generator_cbf77aa253ac.py')]}
# Private metadata differences must not defeat duplicate public-payload handling.
a={'train':[{'input':[[1]],'output':[[1]]}],'test':[{'input':[[2]],'output':[[2]]}],'seed':1}
b=deepcopy(a); b['seed']=2; b['test'][0]['output']=[[9]]
with tempfile.TemporaryDirectory() as temp:
 out=Path(temp)/'duplicate'
 try: p.write_batch([a,b],out); status='accepted'
 except Exception as exc: status=type(exc).__name__+': '+str(exc)
 results['checks']['private_distinct_duplicate']={'result':status,'created_directory':out.exists()}
 if not status.startswith('ValueError: duplicate'): results['findings'].append({'severity':'minor','location':'prototype.py write_batch prepared=sorted(...)','issue':'Equal public bytes but different private metadata cause tuple sort to compare dicts and raise TypeError before intended duplicate rejection.','actual':status,'fix':'Sort prepared tuples with key=lambda row: row[0], then reject duplicate IDs.'})
# Bounded sampler adversary, covering maximum counts and seed endpoints.
count=0
for seed in list(range(60))+[2**64-1]:
 sample=p.sample_inputs(seed,demo_count=12,query_count=8,attempt_limit=1)
 assert len({json.dumps(g) for g in sample['train']+sample['test']})==20
 for grid in sample['train']+sample['test']:
  analysis=p.base._analysis(grid); assert not analysis['errors']; assert len(analysis['plans'])==1
  plan=analysis['plans'][0]; assert min(plan['negative_count'],plan['positive_count'])>0; assert plan['negative_count']!=plan['positive_count']
  colors={c:sum(row.count(c) for row in grid) for c in range(1,10) if c!=4}; ordered=sorted(colors.values(),reverse=True); assert ordered[0]>ordered[1]
  for policy in p.SETTINGS:
   output,clipped=p.python_prediction(grid,policy,with_clipped=True); assert not clipped
  count+=1
results['checks']['sampler_boundary_scenes']=count
with p.RacketBridge(timeout=10) as bridge:
 eps=[p.build_episode(2**64-1,side_policy=s,demo_count=12,query_count=8,attempt_limit=1,bridge=bridge) for s in p.SETTINGS]
 for ep in eps: assert ep['certificate']['survivors']==['setting:'+ep['side_policy']]
 for split in ['train','test']: assert [pair['input'] for pair in eps[0][split]]==[pair['input'] for pair in eps[1][split]]
 with tempfile.TemporaryDirectory() as temp:
  out=Path(temp)/'export'; manifest=p.write_batch(eps,out)
  for ep in eps:
   raw=(out/'public'/(p.public_challenge_id(ep)+'.json')).read_bytes(); assert raw==p.public_challenge_bytes(ep)
   public=json.loads(raw); assert set(public)=={'train','test'}; assert all(set(pair)=={'input'} for pair in public['test'])
 results['checks']['racket_extreme_episodes']={'count':2,'demos_each':12,'queries_each':8,'all_declared_rivals_executed':True,'public_bytes_verified':True}
results['elapsed_seconds']=round(time.monotonic()-t,3)
Path('../checks/adversarial/results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
