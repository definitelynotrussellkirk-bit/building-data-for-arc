"""One bounded audit witness replay; source identities are deliberately separate."""
import hashlib,json,pathlib,signal,subprocess,sys,time
signal.alarm(110)
START=time.monotonic()
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[2]/'repo'
TASK='77181d1aa16c'
OLD='422aaf8f620cefc3e6c86e3e1753dbfa6873ca5dcd0136ee8d32817dfbda53d5'
CURRENT='3300eb415d4a3cc51834b82a8d35017b6a08042c77af77df1b0efd1c4d5423ed'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,v):(HERE/name).write_text(json.dumps(v,indent=2)+'\n')
def keyed(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
home=REPO/'generators'/TASK
idx=home/'evidence/review_index.json'
manifest=home/'counterexamples/review-9bcf85b162267497-v0001/audit_assets.json'
assert sha(idx)=='991ac80fea769294be5f29b0159381950cf9884c2cd6c39d153667a70d40a266'
assert sha(manifest)=='a6893d5a49eba2b012f7dd4e56b83d86e4e28b30f97162e913fa4553a00a70be'
audit=next(a for a in json.loads(idx.read_text())['audits'] if a['return_id']=='review-9bcf85b162267497:v0001')
assert keyed(audit)=='de81f16e9aa4fe7a88f9525b32d794916f844ffa3af3d8a2173b62f72faaea9c'
m=json.loads(manifest.read_text());assert m['audited_generator_sha256']==OLD
assets=[];paths={}
for f in m['files']:
 p=REPO/f['path'];assert sha(p)==f['sha256'] and p.stat().st_size==f['bytes']
 assets.append({'path':f['path'],'sha256':sha(p),'bytes':p.stat().st_size,'verified':True});paths[p.name]=p
sources=[{'path':str(p.relative_to(REPO)),'sha256':sha(p)} for p in home.rglob('*.py') if p.name=='generator.py']
assert not any(s['sha256']==OLD for s in sources),'Historical source unexpectedly available; reassess before execution'
assert sha(home/'generator.py')==CURRENT
sys.path.insert(0,str(REPO/'shared/runtime'))
from reviewer_support import load_selected_generator
gen,source,digest=load_selected_generator(TASK,root=REPO)
assert digest==CURRENT and source==home/'generator.py'
cases=json.loads(paths['cases.json'].read_text())
retained_racket=json.loads(paths['racket.json'].read_text())
assert retained_racket['generator_sha256']==OLD and retained_racket['executed_rule_hash']=='76ff7f3a7ec0'
canonical=[(i,c) for i,c in enumerate(cases) if c['kind']=='canonical']
override=[(i,c) for i,c in enumerate(cases) if c['kind']=='supported_override'];assert len(canonical)==4 and len(override)==1
checks=[]
for i,c in canonical+override:
 checks.append({'name':c['name'],'retained_case_index':i,'input_sha256':keyed(c['input']),'retained_old_self_check':c['self_check'],'current_self_check':gen.self_check(c['input']),'retained_output_sha256':keyed(retained_racket['results'][i]['output'])})
c=override[0][1]
try:
 grid=gen.generate(c['seed'],c['sample_index'],difficulty=c['difficulty'],**c['overrides'])
 override_result={'raised':False,'shape':[len(grid),len(grid[0])]}
except Exception as e:override_result={'raised':True,'type':type(e).__name__,'message':str(e)}
# A single profile-0 sample directly checks construction support for canonical padding.
grid=gen.generate(77181,0,difficulty='hard')
profile={'seed':77181,'sample_index':0,'difficulty':'hard','overrides':{},'shape':[len(grid),len(grid[0])],'source_rectangle':list(gen._largest_nonzero_rect(grid)),'self_check':gen.self_check(grid)}
inputs=[c['input'] for _,c in canonical+override]+[grid]
dump('witness-inputs.json',inputs)
argv=[sys.executable,'-m','arcpuzzles','apply',TASK,'--input',str(HERE/'witness-inputs.json'),'--out',str(HERE/'racket-current.json')]
p=subprocess.run(argv,cwd=REPO,text=True,capture_output=True,timeout=85)
dump('racket-command.json',{'argv':argv,'cwd':str(REPO),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
assert p.returncode==0,p.stderr
actual=json.loads((HERE/'racket-current.json').read_text())
assert actual['generator_sha256']==CURRENT and actual['executed_rule_hash']=='76ff7f3a7ec0'
for row,answer in zip(checks,actual['results']):
 assert answer['error'] is None and answer['valid_output']
 row['current_racket_equals_retained_output']=keyed(answer['output'])==row['retained_output_sha256']
profile['current_racket_valid_output']=actual['results'][-1]['valid_output']
profile['current_model_equals_racket']=gen.rule_mirror(grid)==actual['results'][-1]['output']
result={'ticket_id':'ticket-c214f94c1f5087c9','audited_old_generator_sha256':OLD,'current_generator_sha256':CURRENT,'audit_record_sha256':keyed(audit),'asset_verification':assets,'target_local_generator_sources':sources,'original_reproduction':{'status':'blocked','reason':'The retained manifest and target-local files have no generator source with audited SHA-256 422aaf8f620cefc3e6c86e3e1753dbfa6873ca5dcd0136ee8d32817dfbda53d5. Historical validator and sampler cannot be re-executed from retained evidence alone.','retained_evidence_only':{'canonical_accepted':[0,8],'override_requested':[6,6],'override_observed':[10,10]}},'current_bounded_check':{'canonical_and_override_witnesses':checks,'exact_old_override_call':override_result,'current_declares_old_grid_axes':any(k in gen.AXES for k in ('grid_h','grid_w')),'canonical_padding_construction_sample':profile,'racket_input_count':len(inputs),'scope':'Four retained distinct canonical inputs, one retained old override input, the exact old override call, and one current canonical-padding sample. No historical source execution, broad battery, schedule census, or audit clearance.'},'audit_resolution_changed':False,'probe_elapsed_seconds':time.monotonic()-START}
dump('replay-result.json',result)
print(json.dumps({'original_reproduction':'blocked','current_canonical_acceptance':[sum(not x['current_self_check'] for x in checks[:4]),4],'current_retained_override_acceptance':not checks[-1]['current_self_check'],'current_racket_retained_agreement':[sum(x['current_racket_equals_retained_output'] for x in checks),len(checks)],'old_override_call_current_result':override_result,'current_padding_sample':profile,'probe_elapsed_seconds':result['probe_elapsed_seconds']}))
