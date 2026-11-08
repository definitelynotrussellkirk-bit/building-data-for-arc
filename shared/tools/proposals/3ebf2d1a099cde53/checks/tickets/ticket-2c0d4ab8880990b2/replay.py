from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
REPO=WORK/'repo'
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
TASK='0c2ab7de69d1'
SOURCE_SHA='aae633b9d9b4dd317998f47490cd9b84b8ce701bc6c91d4fcc48e8ca5e6c6d75'
SCRIPT_SHA='1e56db79506a8a1178ee1228725dc425290a9694afa7be52b14d9ffc0ce9e387'
RULE_HASH='ca5f7e2b1e40'
source=REPO/f'generators/{TASK}/generator.py'
assert sha(source)==SOURCE_SHA
assert sha(HERE/'retained_find_counterexample.py')==SCRIPT_SHA
completed=subprocess.run([sys.executable,str(HERE/'retained_find_counterexample.py')],cwd=REPO,text=True,capture_output=True,timeout=70,check=False)
(HERE/'probe.stdout.log').write_text(completed.stdout)
(HERE/'probe.stderr.log').write_text(completed.stderr)
assert completed.returncode==0,(completed.stdout,completed.stderr)
retained=REPO/f'generators/{TASK}/counterexamples/review-529f49df89b85e1d-v0001/retained/checks/audit/{TASK}'
for name in ('input.json','rival_outputs.json','search_report.json'):
    assert (HERE/name).read_bytes()==(retained/name).read_bytes(),name
search=json.loads((HERE/'search_report.json').read_text())
assert search['seed']==0 and search['difficulty']=='medium'
assert search['demonstrations_fit_rival_python_mirror']==[True,True,True]
assert search['query_disagrees_python_mirror'] is True
assert search['all_inputs_pass_self_check'] is True
inputs=json.loads((HERE/'input.json').read_text())
rivals=json.loads((HERE/'rival_outputs.json').read_text())
from puzzle_generators import runner
bundle=runner._load_bundle(TASK)
normalized=hashlib.sha256(' '.join(bundle.rule_source.split()).encode()).hexdigest()[:12]
assert normalized==RULE_HASH
bridge,name=runner._open_bridge_with_rule(bundle.rule_callable_text)
try:
    outputs=[runner._apply_rule(bridge,name,grid) for grid in inputs]
    runtime=bridge.runtime_identity
finally:
    bridge.shutdown()
diffs=[]
agreements=[]
for expected,rival in zip(outputs,rivals):
    cells=[[r,c,expected[r][c],rival[r][c]] for r in range(len(expected)) for c in range(len(expected[0])) if expected[r][c]!=rival[r][c]]
    diffs.append(cells); agreements.append(not cells)
assert agreements[:3]==[True,True,True]
assert agreements[3] is False
assert diffs[3]==[[6,1,5,8],[6,2,5,8],[6,3,5,8]]
authority={
 'executed_rule_hash':normalized,
 'protected_racket':runtime['protected'],
 'demonstration_agreements':agreements[:3],
 'query_agreement':agreements[3],
 'query_differences':diffs[3],
 'outputs':outputs,
}
(HERE/'racket_replay.json').write_text(json.dumps(authority,sort_keys=True,indent=2)+'\n')
result={
 'schema':'arcpuzzles-ticket-adversarial-witness-v1',
 'ticket_id':HERE.name,
 'status':'finding',
 'task_id':TASK,
 'generator_sha256':SOURCE_SHA,
 'rule_hash':RULE_HASH,
 'plausible_shortcut':'Reflect every eligible above-divider source even when its destination is occupied.',
 'witness':{
   'seed':0,'difficulty':'medium','demonstrations':[0,1,2],'query':3,
   'all_inputs_lawful':True,'demos_fit_rival':[True,True,True],
   'query_refutes_rival':True,'query_differences':diffs[3],
 },
 'retained_witness_reproduced_byte_exact':True,
 'protected_racket_authority_reproduced':True,
 'limitations':['One deterministic four-pair lesson witness; no peer battery or census.','Finding remains source-bound and requires maintainer triage.'],
}
(HERE/'receipt.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({'ticket_id':HERE.name,'status':'finding','query_differences':diffs[3]},sort_keys=True))
