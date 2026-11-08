from pathlib import Path
import copy, hashlib, importlib.util, json, os, sys, time
WORK=Path(__file__).resolve().parents[2]
REPO=WORK/'repo'
p=REPO/'generators/c4f6a0585dbf/workspace/parametric/port_threshold.py'
spec=importlib.util.spec_from_file_location('independent_threshold',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
started=time.monotonic();out=Path(__file__).parent/'final';out.mkdir();checks=[]
for override in [dict(seed=True),dict(n_train=False),dict(n_test=1.0),dict(max_attempts=0),dict(min_visible_ports=True),dict(seed=-1)]:
 args=dict(seed=583,n_train=1,n_test=4,min_visible_ports=2);args.update(override)
 try:m.generate_episode(**args)
 except ValueError:checks.append({'case':'reject_invalid_numeric','override':override,'passed':True})
 else:raise AssertionError(('accepted invalid',override))
try:m.generate_episode(seed=583,n_train=1,n_test=4,max_attempts=1)
except m.SamplingExhausted:checks.append({'case':'retry_exhaustion_no_short_batch','passed':True})
else:raise AssertionError('short attempt limit did not fail')
with m.RacketOracle() as oracle:
 episodes=[m.generate_episode(seed=583,min_visible_ports=t,n_train=1,n_test=4,oracle=oracle) for t in (2,3)]
 for ep in episodes:
  identities=[m.grid_sha256(x['input']) for x in ep['train']+ep['test']]
  assert len(identities)==len(set(identities))==5
  assert ep['certificate']['surviving_parameters']==[ep['parameters']['min_visible_ports']]
  assert all(x['identified'] for x in ep['certificate']['queries'])
  checks.append({'case':'fresh_seed_distinct_and_demo_identified','threshold':ep['parameters']['min_visible_ports'],'train':1,'queries':4,'passed':True})
 altered=copy.deepcopy(episodes)
 for ep in altered:
  ep['seed']=999999;ep['private_note']='private-change'
  for pair in ep['test']:pair['output']=[[9]]
  assert m.public_challenge_id(ep)==m.public_challenge_id(episodes[altered.index(ep)])
 m.write_batch(episodes,out/'public-a');m.write_batch(altered,out/'public-b')
 a={p.name:p.read_bytes() for p in (out/'public-a/public').iterdir()};b={p.name:p.read_bytes() for p in (out/'public-b/public').iterdir()}
 assert a==b
 ids=json.loads((out/'public-a/private/export.json').read_text())['public_ids']
 assert ids==sorted(ids)
 assert all(hashlib.sha256(raw).hexdigest()+'.json'==name for name,raw in a.items())
 checks.append({'case':'writer_private_mutations_leave_public_bytes_and_names_unchanged','passed':True})
 try:m.write_batch([episodes[0],copy.deepcopy(episodes[0])],out/'duplicate')
 except ValueError:assert not (out/'duplicate').exists()
 else:raise AssertionError('duplicate challenge accepted')
 checks.append({'case':'duplicate_rejected_before_output_creation','passed':True})
 receipt={'status':'pass','command':[sys.executable,str(Path(__file__))],'cwd':str(Path.cwd()),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256((REPO/'generators/c4f6a0585dbf/generator.py').read_bytes()).hexdigest(),'racket_evaluations':oracle.evaluations,'elapsed_seconds':time.monotonic()-started,'whole_adversarial_elapsed_seconds':time.monotonic()-json.loads((out.parent/'start.json').read_text())['started_monotonic'],'checks':checks,'scope':'Two surfaces: numeric/retry boundaries and public/private export; fresh seed has one demonstration/four queries per setting; no universal identifiability claim. Query-answer mutations test public identity only, not a private-label verifier.'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ['status','racket_evaluations','elapsed_seconds']}))
