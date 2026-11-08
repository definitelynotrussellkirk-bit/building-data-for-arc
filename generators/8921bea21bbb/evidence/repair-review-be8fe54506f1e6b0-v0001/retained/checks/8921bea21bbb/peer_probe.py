from pathlib import Path
import hashlib,json
from reviewer_support import load_selected_generator,canonical_path
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
ROOT=Path.cwd(); TASK='8921bea21bbb'; OUT=ROOT.parent/'checks'/TASK
G,S,H=load_selected_generator(TASK,root=ROOT)
assert H=='987e6c00f0a6a7066e11f454d5680b5aa140806dbb8d55ccbbf883a6f6f8c462',H
rows=[json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get('task_id')==TASK]
assert len(rows)==1,len(rows)
program=rows[0]['program_solution']; program_sha=hashlib.sha256(program.encode()).hexdigest()
def sexpr(x):return '('+' '.join(sexpr(v) if isinstance(v,list) else str(v) for v in x)+')'
def rival(grid):
 w=(len(grid[0])-1)//2
 return [[row[w+1+c] if row[c] in (2,3) else 0 for c in range(w)] for row in grid]
pairs=[]
with RacketBridge() as bridge:
 identity=bridge.runtime_identity
 assert identity.get('protected') is True,identity
 for i in range(4):
  grid=G.generate(404,i,difficulty='easy')
  label=bridge.eval_text(f"({wrap_rule(program)} '{sexpr(grid)})")
  assert label==G.rule_mirror(grid),(i,label)
  assert G.self_check(grid)==[],i
  pairs.append({'input':grid,'output':label,'sample_index':i,'mask_color':G.observe_overrides(grid)['mask_color']})
demos=pairs[:3];query=pairs[3]
assert all(rival(p['input'])==p['output'] for p in demos)
assert rival(query['input'])!=query['output']
assert G.lesson_identifiable(demos,query)==[]
result={'task_id':TASK,'generator_sha256':H,'canonical_rule_hash':G.RULE_HASH,'program_solution_sha256':program_sha,'runtime_identity':identity,'command':'WORK/.venv/bin/python review.py run python3 ../checks/8921bea21bbb/peer_probe.py','launcher_cwd':str(ROOT.parent.parent),'payload_cwd':str(ROOT),'exit_code':0,'seed':404,'difficulty':'easy','rival':'copy corresponding right value iff left color is 2 or 3, else 0','finding':'Rival fits all three generated demonstrations but disagrees on color-7 query. Existing lesson_identifiable returns [] because this rival is undeclared.','demos':demos,'query':query,'rival_query_output':rival(query['input']),'limits':'One four-pair default lesson. Fixed-color rival is a plausible color-sensitive extrapolation alternative, not a universal semantic uniqueness criterion. No batteries, assignments, source, reference rule, admission, or approval changes.'}
(OUT/'finding.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['task_id','generator_sha256','program_solution_sha256','finding','exit_code']}))
