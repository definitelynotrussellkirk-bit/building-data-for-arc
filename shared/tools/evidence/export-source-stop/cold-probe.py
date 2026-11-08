from pathlib import Path
import sys,os,json,hashlib
suffix=sys.argv[1] if len(sys.argv)>1 else '';root=Path(__file__).resolve().parent;repo=root/'checkout/WORK/repo';sys.path[:0]=[str(repo/'src'),str(repo/'shared/runtime')]
os.environ['RACKET_PATH']=str(root/'checkout/WORK/.review/racket-runtime/racket/bin/racket')
from arcpuzzles import Catalog,datasets,parametric_promotion as promotion
from arcpuzzles.catalog import jsonl
c=Catalog(repo);tid='57bafcdde8c3';adapter=repo/f'generators/{tid}/workspace/parametric/adapter.py';before=adapter.read_bytes();accepted=promotion.status(c,tid);assert accepted['status']=='accepted'
original=Catalog.generate_parametric;execute=promotion._execute;observed=[];attempts=[]
def observe(*args,**kwargs):
 value=execute(*args,**kwargs);assert value['racket']['backend']=='racket' and value['racket']['protected'] is True
 observed.append({'racket_evaluations':value['racket_evaluations'],'runtime':value['racket']});return value
promotion._execute=observe

def drift(self,*args,**kwargs):
 attempts.append(kwargs['seed'])
 if len(attempts)==2:adapter.write_bytes(before+b'\n# intentional cold source drift\n')
 return original(self,*args,**kwargs)
Catalog.generate_parametric=drift
try:
 output=root/('source-stop-partial'+suffix);result=c.export(output,count=3,seed=17,task_ids=[tid],style='episodes',accepted_parameters=True,n_train=3,n_test=4,max_attempts=9)
 assert result['status']=='incomplete' and result['accepted_episodes']==1 and result['attempted_episodes']==2
 assert result['stop_reason']['kind']=='accepted_parameter_snapshot_invalid' and len(attempts)==2
 failures=jsonl(output/'rejections.jsonl');assert len(failures)==1 and failures[0]['retryable'] is False
 episodes=jsonl(output/'episodes.private.jsonl');assert len(episodes)==1 and len(episodes[0]['test'])==4
 assert result['files']['public.jsonl']['sha256']==hashlib.sha256((output/'public.jsonl').read_bytes()).hexdigest()
 assert len(observed)==1 and observed[0]['racket_evaluations']==22
 try:datasets.verify_dataset(output)
 except ValueError as error:assert 'not a complete' in str(error)
 else:raise AssertionError('An incomplete batch was accepted by serialized verification')
finally:
 adapter.write_bytes(before);Catalog.generate_parametric=original
assert promotion.status(Catalog(repo),tid)['acceptance_sha256']==accepted['acceptance_sha256']
retries=[]
def bounded(self,*args,**kwargs):retries.append(kwargs['seed']);raise ValueError('deliberate bounded sampler exhaustion')
Catalog.generate_parametric=bounded
try:
 retry=c.export(root/('source-stop-retry'+suffix),count=1,seed=17,task_ids=[tid],style='episodes',accepted_parameters=True,n_train=3,n_test=4,max_attempts=3)
 assert retry['status']=='incomplete' and retry['attempted_episodes']==3 and len(retries)==3
 assert 'stop_reason' not in retry and len(observed)==1
finally:Catalog.generate_parametric=original;promotion._execute=execute
report={'schema':'arcpuzzles-cold-source-stop-probe-v1','status':'passed','task_id':tid,'acceptance_sha256':accepted['acceptance_sha256'],'drift':{'attempts':2,'accepted_episodes':1,'query_labels':4,'rejections':1,'stop_reason':result['stop_reason'],'partial_manifest_hashed':True,'incomplete_serialized_export_refused':True},'bounded_sampler':{'attempts':3,'early_stop':False,'reference_execution':False},'real_worker_observations':observed,'selected_adapter_restored_sha256':hashlib.sha256(before).hexdigest(),'owner_reads_denied_by_harness':True,'training_admitted':False,'scope':'Read-confined fresh packet/venv/bundled Racket. One real accepted episode; deliberate mutation only in cold adapter copy before draw2; exact bytes restored. Spy forwards worker result unchanged. Bounded sampler failure injected separately; no owner source/rule/approval change.'}
(root/('source-stop-result'+suffix+'.json')).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report))
