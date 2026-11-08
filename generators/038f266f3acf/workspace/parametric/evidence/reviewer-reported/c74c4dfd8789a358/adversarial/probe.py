from pathlib import Path
import copy,hashlib,importlib.util,json,os,sys,tempfile,time,traceback
W=Path(__file__).resolve().parents[2];REPO=W/'repo';D=Path(__file__).parent
P=REPO/'generators/038f266f3acf/workspace/parametric/beam_width.py'
spec=importlib.util.spec_from_file_location('independent_beam_probe',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[];start=time.monotonic();receipt={'command':[sys.executable,str(Path(__file__).resolve())],'cwd':str(Path.cwd()),'source_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256((REPO/'generators/038f266f3acf/generator.py').read_bytes()).hexdigest(),'scope':'Independent bounded query/certificate and numeric/retry/public-projection checks; identity mutations are not private-label validation.'}
def check(name,condition,**data):
 assert condition,name
 checks.append({'case':name,'passed':True,**data})
class Query(dict):
 def __getitem__(self,key):
  if key=='output':raise AssertionError('held-out output accessed')
  return super().__getitem__(key)
try:
 for override in [{'seed':True},{'wing_multiplier':True},{'n_train':1.0},{'n_test':False},{'n_test':17},{'max_attempts':0}]:
  args={'seed':842,'wing_multiplier':1,'n_train':1,'n_test':4};args.update(override)
  try:m.generate_episode(**args)
  except ValueError:check('strict_numeric_rejection',True,override=override)
  else:raise AssertionError('invalid arguments accepted')
 try:m.generate_episode(seed=842,wing_multiplier=1,n_train=1,n_test=4,max_attempts=1)
 except m.SamplingExhausted:check('exhaustion_never_short_returns',True)
 else:raise AssertionError('insufficient attempt budget accepted')
 with m.RacketOracle() as oracle:
  episodes=[m.generate_episode(seed=842,wing_multiplier=v,n_train=1,n_test=4,oracle=oracle) for v in (1,2)]
  for ep in episodes:
   value=ep['parameters']['wing_multiplier'];pairs=ep['train']+ep['test']
   check('fresh_seed_distinct_inputs',len({m.grid_sha256(p['input']) for p in pairs})==5,multiplier=value)
   query=[Query(input=p['input']) for p in ep['test']]
   cert=m.certify_episode(ep['train'],query,oracle)
   check('demo_only_certificate',cert==ep['certificate'] and cert['surviving_models']==[f'multiplier_{value}'] and not cert['surviving_cap_rivals'] and all(r['identified'] for r in cert['queries']),multiplier=value)
   check('deep_objects_and_cap_witnesses',all(sorted(s['source_depths'])==[5,6] and all(n>0 for n in s['cap_four_disagreement_cells'].values()) for s in ep['sampling']['accepted']),multiplier=value)
  g=m.selected_generator();demos=[]
  for i in range(4):
   grid=g.generate(20261012,i,difficulty='easy');demos.append({'input':grid,'output':oracle.evaluate(grid,'multiplier_1')})
  raw=json.loads((REPO/'generators/038f266f3acf/counterexamples/review-c163cb377b0acf2c-v0001/retained/checks/audit/038f266f3acf/canonical_input.json').read_text())
  grid=raw.get('input',raw) if isinstance(raw,dict) else raw
  pred=oracle.evaluate(grid,'multiplier_1');cap=oracle.evaluate(grid,'multiplier_1_cap_depth_4')
  diff=sum(a!=b for ra,rb in zip(pred,cap) for a,b in zip(ra,rb))
  reasons=g.lesson_identifiable(demos,Query(input=grid))
  check('canonical_28_cell_guard_uses_no_query_answer',diff==28 and any('cap 4' in x for x in reasons),differing_cells=diff,reasons=reasons)
  receipt['racket_evaluations']=oracle.evaluations
  (D/'witness-episodes.jsonl').write_text(''.join(json.dumps(ep,sort_keys=True,separators=(',',':'))+'\n' for ep in episodes))
 with tempfile.TemporaryDirectory(prefix='export-probe-',dir=D) as tmp:
  t=Path(tmp);a=m.write_batch(episodes,t/'a')
  changed=copy.deepcopy(episodes)
  for ep in changed:
   ep['seed']=999999;ep['private_note']='hidden only'
   for pair in ep['test']:pair['output']=[[9]]
  b=m.write_batch(changed,t/'b')
  first={p.name:p.read_bytes() for p in (t/'a/public').iterdir()};second={p.name:p.read_bytes() for p in (t/'b/public').iterdir()}
  check('private_seed_and_answer_mutations_preserve_exact_public_bytes',first==second and a['public_ids']==b['public_ids']==sorted(a['public_ids']))
  check('exact_visible_content_hash_names',all(hashlib.sha256(raw).hexdigest()+'.json'==name for name,raw in first.items()))
  try:m.write_batch([episodes[0],copy.deepcopy(episodes[0])],t/'duplicate')
  except ValueError:check('duplicate_rejected_before_creation',not(t/'duplicate').exists())
  else:raise AssertionError('duplicate public payload accepted')
 receipt.update(status='pass',exit_code=0,checks=checks)
except BaseException as e:
 receipt.update(status='failed',exit_code=1,checks=checks,error=f'{type(e).__name__}: {e}',traceback=traceback.format_exc())
 raise
finally:
 receipt['elapsed_seconds']=time.monotonic()-start
 receipt['whole_review_elapsed_seconds']=time.monotonic()-json.loads((D/'start.json').read_text())['start_monotonic']
 (D/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:v for k,v in receipt.items() if k not in ['traceback','checks']},indent=2))
