"""One source-bound allocation probe: 3 demos, 4 queries, actual Racket labels.
This is a user-requested supplemental ticket, not an official assignment draw.
"""
from __future__ import annotations
import argparse,hashlib,json,os,tempfile,time
from pathlib import Path
from reviewer_support import find_root,canonical_path,load_selected_generator,public_challenge_bytes,public_challenge_id
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()

p=argparse.ArgumentParser()
p.add_argument('--seed',type=int,required=True)
p.add_argument('--profile-id',type=int,default=4)
p.add_argument('--demo-count',type=int,default=3)
p.add_argument('--query-count',type=int,default=4)
args=p.parse_args()
if args.demo_count<3 or args.query_count<1 or args.demo_count+args.query_count>12:p.error('require >=3 demos, >=1 query and <=12 total pairs')
out=Path(__file__).resolve().parent;root=find_root(__file__)
tempfile.tempdir=str(out);os.environ['TMPDIR']=str(out)
start=time.monotonic()
report={'schema':'user-requested-allocation-probe-v1','task_id':'be5d9fa6fec1','ticket_id':'extra-ticket-61127ac40e9a0a16','status':'unknown','arguments':vars(args),'probe_sha256':sha(Path(__file__).read_bytes()),'query_answers_used_for_rival_elimination':False}
try:
 selected=json.loads((out/'selection.json').read_text())['selected']
 gen,path,source_hash=load_selected_generator(selected['task_id'],root=root)
 assert source_hash==selected['generator_sha256'],'source drift'
 report['source_sha256']=source_hash
 programs={row['program_solution'] for row in map(json.loads,canonical_path(root).read_text().splitlines()) if row.get('task_id')==selected['rule_task_id']}
 assert len(programs)==1,'ambiguous canonical rule'
 program=programs.pop();rule_hash=sha(' '.join(program.split()).encode())[:12]
 assert rule_hash==selected['rule_hash'],'canonical rule drift'
 callable_text=wrap_rule(program)
 report.update({'rule_hash':rule_hash,'canonical_text_sha256':sha(program.encode()),'callable_text_sha256':sha(callable_text.encode())})
 (out/'canonical_rule.rkt').write_text(program)
 build_started=time.monotonic()
 grids=[gen.generate(args.seed,i,profile_id=args.profile_id) for i in range(args.demo_count+args.query_count)]
 errors=[gen.self_check(g) for g in grids]
 report.update({'generation_seconds':round(time.monotonic()-build_started,6),'validation_errors':errors})
 assert not any(errors),'source validation failure'
 assert len({canonical(g) for g in grids})==len(grids),'duplicate demo/query input'
 assert all(len(g)==22 and len(g[0])==4 for g in grids) if args.profile_id==4 else True
 bridge_started=time.monotonic();bridge=RacketBridge(timeout=15,startup_timeout=45)
 try:
  report['racket_startup_seconds']=round(time.monotonic()-bridge_started,6)
  bridge.eval_text(f'(define allocation_rule {callable_text})')
  label_started=time.monotonic();outputs=[]
  for g in grids:
   bridge.define_grid('allocation_input',g)
   outputs.append(bridge.eval_text('(allocation_rule allocation_input)'))
  report['racket_label_seconds']=round(time.monotonic()-label_started,6)
  report['runtime_identity']=bridge.runtime_identity
 finally:bridge.close()
 assert all(gen.rule_mirror(g)==a for g,a in zip(grids,outputs)),'Python/Racket mismatch'
 pairs=[{'input':g,'output':a} for g,a in zip(grids,outputs)]
 demos=pairs[:args.demo_count];queries=pairs[args.demo_count:]
 rival_fits={name:[rival(d['input'])==d['output'] for d in demos] for name,rival in gen.LESSON_COMPETITORS.items()}
 surviving=[name for name,fits in rival_fits.items() if all(fits)]
 identifiability=[gen.lesson_identifiable(demos,q['input']) for q in queries]
 report.update({'demo_count':len(demos),'query_count':len(queries),'all_inputs_distinct':True,'rival_demo_fits':rival_fits,'surviving_named_rivals':surviving,'per_query_identifiability_errors':identifiability})
 assert not surviving and not any(identifiability),'declared rival survives demonstrations'
 challenge={'train':demos,'test':queries}
 (out/'private_episode.json').write_text(json.dumps({'task_id':selected['task_id'],'seed':args.seed,'source_sha256':source_hash,'rule_hash':rule_hash,'profile_id':args.profile_id,**challenge},indent=2)+'\n')
 public=out/'public';public.mkdir(exist_ok=True)
 public_name=public_challenge_id(challenge)+'.json'
 (public/public_name).write_bytes(public_challenge_bytes(challenge))
 report.update({'status':'completed','racket_labels_checked':len(outputs),'python_racket_parity':True,'input_shapes':[[len(g),len(g[0])] for g in grids],'output_shapes':[[len(g),len(g[0])] for g in outputs],'input_sha256':[sha(canonical(g)) for g in grids],'query_output_sha256':[sha(canonical(q['output'])) for q in queries],'public_path':'public/'+public_name,'public_sha256':sha((public/public_name).read_bytes()),'scope':'One seven-input episode, one production source override profile_id=4. Direct selected-generator and canonical-Racket probe, not a public CLI generate or full-corpus coverage claim.'})
except Exception as error:
 report.update({'status':'blocked','error_type':type(error).__name__,'error':str(error)})
 raise
finally:
 report['elapsed_seconds']=round(time.monotonic()-start,6)
 (out/'probe_result.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:report.get(k) for k in ['status','demo_count','query_count','racket_labels_checked','surviving_named_rivals','elapsed_seconds','error']},sort_keys=True))
