"""Replay only the stored supported-count median-palette counterexamples."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
root=next(p for p in Path(__file__).resolve().parents if(p/'catalog/puzzles.jsonl').is_file())
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
if args.out.exists()or args.out.is_symlink():raise FileExistsError(args.out)
home=root/'generators/7d1e8744229a';evidence=json.loads(Path(__file__).with_name('evidence.json').read_text());assessment=json.loads(Path(__file__).with_name('assessment.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(home/'generator.py')==assessment['generator_sha256']
for row in evidence['source_binding']['files']:
 p=row['path']
 if p.startswith('generators/7d1e8744229a/workspace/parametric/')and (p.endswith(('.py','.rkt'))or p.endswith('/promotion.json')):assert sha(root/p)==row['sha256'],p
count=0
with _local_imports(root/'shared/runtime',home):
 spec=importlib.util.spec_from_file_location('supported_count_adapter',home/'workspace/parametric/adapter.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter);apply,identity,bridge=_real_evaluator(root/'shared/runtime')
 try:
  for scope in evidence['scopes']:
   program=adapter.program({'mode':scope['mode']});assert hashlib.sha256(program.encode()).hexdigest()==scope['program_sha256'];pairs=scope['inputs'];outputs=[_grid(apply(program,p['input']))for p in pairs];count+=len(pairs);assert outputs==[p['output']for p in pairs]
   for rival in scope['rivals']:
    program=rival['program'];assert hashlib.sha256(program.encode()).hexdigest()==rival['program_sha256'];actual=[_grid(apply(program,p['input']))for p in pairs];count+=len(pairs);d=scope['demos'];matches=[a==b for a,b in zip(outputs[:d],actual[:d])];changed=[i for i,(a,b)in enumerate(zip(outputs[d:],actual[d:]))if a!=b];assert matches==rival['demo_matches'];assert changed==rival['query_changed_indices'];assert not(all(matches)and changed)
 finally:bridge.close()
report=dict(status='passed',protected_evaluations=count,scopes=len(evidence['scopes']),scope='Stored supported-count lessons and named rivals only; original two-demo finding retained.',racket=identity);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
