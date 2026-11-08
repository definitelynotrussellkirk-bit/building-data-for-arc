#!/usr/bin/env python3
from __future__ import annotations
import argparse,ast,contextlib,copy,hashlib,io,json,pathlib,shlex,subprocess,sys,time,types,zipfile
from typing import Any
STARTED_EPOCH=1792748761.5018055
WORK=pathlib.Path('/dev/shm/arc_review_9f2ab2a3546c/WORK')
REPO=WORK/'repo'
OUT=pathlib.Path(__file__).resolve().parent
TICKET='ticket-4d1d2f2f60a1092c'
TASK='019445e9b5a1'
REQUEST='review-012cfa1a42bc531d:v0001:F3'
SEED='3da4e08c862a0a0180fae44ebada216b0786b12e9e39cff24564e86b97e6871e'
ARCHIVE=pathlib.Path('/workspace/scratch/9f2ab2a3546c/upload/SEND-THIS-ARCpuzzles-review(5).zip')
ASSET='WORK/repo/shared/tools/proposals/6024f0a6785f56fd/checks/before/checks/019445e9b5a1_before_profile_floor.json'
checks=[]
probe_started=time.monotonic()
def sha(data):return hashlib.sha256(data).hexdigest()
def write(name,value):
 (OUT/name).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def require(condition,description):
 checks.append({'check':description,'passed':bool(condition)})
 if not condition:raise AssertionError(description)
def pinned(path,expected):
 data=path.read_bytes();actual=sha(data)
 require(actual==expected,'Pinned SHA-256 matches '+str(path.relative_to(WORK)))
 return data,actual
try:
 manifest_raw,manifest_sha=pinned(REPO/'shared/tools/proposals/6024f0a6785f56fd/manifest.json','956771283f01feb9bba354c14c9ce4b665fc17c15e3e61afc65021d7bd9f7325')
 suggestions_raw,suggestions_sha=pinned(REPO/'REVIEW/suggestions.json','67fdad2e6b3cdd0fa6d8aeeff83afa2790f0fa67260178aab768276cae85e633')
 _,generator_sha=pinned(REPO/'generators/019445e9b5a1/generator.py','a95dfe6dc79eb24c223a6dad735b64117dedae6d0769968e9571bfedbc9a5846')
 request=next(x for x in json.loads(suggestions_raw)['items'] if x['request_id']==REQUEST)
 request_sha=sha(json.dumps(request,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
 require(request_sha=='87155edac0b46c7110d577363ff7633d6a1f2d8c06dd60330fb3f7c08d51a99b','Pinned structured request SHA-256 matches')
 with zipfile.ZipFile(ARCHIVE) as z:asset_raw=z.read(ASSET)
 asset_sha=sha(asset_raw)
 require(asset_sha=='c2f3569b96d37430c255faf9ba213bbf353333cf61edd572c27ccb94f5e12f1d','Retained asset SHA-256 matches manifest')
 (OUT/'retained_profile_floor.json').write_bytes(asset_raw)
 retained=json.loads(asset_raw)['audits'][0]
 require(retained['task_id']==TASK,'Retained task identity matches')
 gate_path=REPO/'shared/tools/canonical_profile_gate.py'
 battery_path=REPO/'shared/tools/run_generator_battery.sh'
 gate_source=gate_path.read_text();battery_source=battery_path.read_text()
 start=battery_source.index('cmd_for() {\n')
 end=battery_source.index('\n}\n',start)+3
 command_function=battery_source[start:end]
 shell=command_function+'\nTASK='+shlex.quote(TASK)+'\nPHASE=before\ncmd_for profile_floor\nPHASE=after\ncmd_for profile_floor\n'
 emitted=subprocess.run(['bash','-c',shell],text=True,capture_output=True,timeout=10,check=True).stdout.splitlines()
 require(len(emitted)==2,'Current command function emits one before and one after profile command')
 before_command,after_command=emitted
 before_argv=shlex.split(before_command.split(';',1)[0])[2:]
 after_argv=shlex.split(after_command)[2:]
 require('--strict' in after_argv and '--require-pass' in after_argv,'After policy enables strict and require-pass')
 floor_index=after_argv.index('--min-band-support')
 require(after_argv[floor_index+1]=='1','After policy enforces minimum one exact hit per band')
 require('ADVISORY-OK' in before_command,'Current before wrapper labels WARN as advisory')
 tree=ast.parse(gate_source,filename=str(gate_path))
 selected={'_profile','_pinned_seed','audit_task','_finish','main'}
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in selected]
 require({n.name for n in nodes}==selected,'Replay compiles the exact current audit and CLI function ASTs')
 def grid(profile):
  h,w,p=profile
  return [[(r*w+c)%p for c in range(w)] for r in range(h)]
 canonical=[grid(p) for p in retained['canonical_profiles']]
 envelope_only=grid((4,7,6))
 outside=grid((1,1,1))
 class RetainedProfileReplay:
  def __init__(self):self.indices={b:0 for b in ('easy','medium','hard')}
  def self_check(self,g):return []
  def generate(self,seed,sample_index,difficulty):
   index=self.indices[difficulty];self.indices[difficulty]+=1
   expected=ns['_pinned_seed'](TASK,difficulty,index)
   if seed!=expected or sample_index!=seed%7919+index:raise AssertionError('Unexpected replay coordinates')
   stats=retained['per_band'][difficulty]
   if index<stats['exact']:return copy.deepcopy(canonical[0])
   if index<stats['envelope']:return copy.deepcopy(envelope_only)
   return copy.deepcopy(outside)
 current=[None]
 def import_replay(name):
  if name!=f'puzzle_generators.per_puzzle.{TASK}.generator':raise AssertionError('Unexpected generator import')
  return current[0]
 ns={'__doc__':ast.get_docstring(tree),'argparse':argparse,'copy':copy,'hashlib':hashlib,'importlib':types.SimpleNamespace(import_module=import_replay),'json':json,'sys':sys,'Path':pathlib.Path,'Any':Any,'BANDS':('easy','medium','hard'),'canonical_inputs':lambda task:copy.deepcopy(canonical)}
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(gate_path),'exec'),ns)
 modes={}
 previous_argv=sys.argv
 try:
  for mode,argv in [('before',before_argv),('after',after_argv)]:
   current[0]=RetainedProfileReplay()
   target=OUT/(mode+'_replay.json')
   args=list(argv);args[args.index('--json-out')+1]=str(target)
   sys.argv=['canonical_profile_gate.py']+args
   capture=io.StringIO()
   with contextlib.redirect_stdout(capture):code=ns['main']()
   audit=json.loads(target.read_text())['audits'][0]
   require(audit['per_band']==retained['per_band'],mode+' replay reproduces every retained per-band count')
   modes[mode]={'exit_code':code,'stdout':capture.getvalue(),'audit':audit,'argv':args}
 finally:sys.argv=previous_argv
 require(modes['before']['exit_code']==0 and modes['before']['audit']['status']=='WARN','Historical advisory condition remains nonblocking only in before policy')
 require(modes['after']['exit_code']!=0 and modes['after']['audit']['status']=='FAIL','Current after policy blocks the retained zero-support-band condition')
 require(modes['after']['audit']['bands_below_floor']==['easy','hard'],'After failure specifically names easy and hard below floor')
 elapsed=(time.time()-STARTED_EPOCH)/60
 result={'ticket_id':TICKET,'request_id':REQUEST,'status':'completed','targeted_probe_count':1,'targeted_probe_seconds':round(time.monotonic()-probe_started,4),'budget_seconds':120,'provided_probe_seed':SEED,'seed_usage':'Deterministic retained-aggregate replay; no new generator samples or random census were run. The unchanged gate still derives and checks its normal pinned coordinates.','method':'Executed the exact current Bash cmd_for function, then compiled unchanged current gate audit/main function ASTs. Replayed synthetic grids reproducing the retained canonical profiles and every per-band morphology count. This tests current policy against retained aggregate evidence; original historical grids are not present in the retained asset.','bindings':{'assets_manifest_sha256':manifest_sha,'suggestions_sha256':suggestions_sha,'request_sha256':request_sha,'generator_sha256':generator_sha,'retained_asset_sha256':asset_sha,'gate_sha256':sha(gate_source.encode()),'battery_sha256':sha(battery_source.encode())},'retained_asset':{'source_zip_member':ASSET,'copied_to':'checks/tickets/'+TICKET+'/retained_profile_floor.json','repo_assets_restored':[]},'current_commands':{'before':before_command,'after':after_command},'replays':modes,'checks':checks,'proposed_request_disposition':'close_as_already_addressed_by_current_selected_battery_policy','scope_limits':['No historical sample-level generator rerun: retained evidence contains aggregate counts only.','No complete battery, peer audit, shared tooling edits, or generator edits were performed.'],'elapsed_minutes':round(elapsed,3)}
 write('probe.json',result)
 outcome={'ticket_id':TICKET,'type':'tool_reproduction','status':'completed','summary':'Pinned retained evidence confirms zero exact support in easy and hard was advisory before. The single bounded replay reproduces those counts: current before policy exits 0/WARN, while current after policy emits --strict --require-pass --min-band-support 1 and exits 2/FAIL for easy and hard. Proposed request disposition: close as already addressed by current selected battery policy. This is an aggregate-policy replay, not a historical sample-level generator rerun.','evidence_paths':['checks/tickets/'+TICKET+'/'+p for p in ['probe.json','probe.py','retained_profile_floor.json','before_replay.json','after_replay.json']],'elapsed_minutes':round(elapsed,3)}
 write('outcome.json',outcome)
 print(json.dumps({'outcome':outcome,'targeted_probe_seconds':result['targeted_probe_seconds'],'before_exit':modes['before']['exit_code'],'after_exit':modes['after']['exit_code'],'assertions_passed':len(checks)},indent=2))
except Exception as exc:
 elapsed=(time.time()-STARTED_EPOCH)/60
 write('probe.json',{'ticket_id':TICKET,'targeted_probe_count':1,'status':'blocked','error':repr(exc),'checks':checks,'targeted_probe_seconds':round(time.monotonic()-probe_started,4)})
 write('outcome.json',{'ticket_id':TICKET,'type':'tool_reproduction','status':'blocked','summary':'Single targeted policy replay was blocked: '+repr(exc),'evidence_paths':['checks/tickets/'+TICKET+'/probe.json','checks/tickets/'+TICKET+'/probe.py'],'elapsed_minutes':round(elapsed,3)})
 raise
