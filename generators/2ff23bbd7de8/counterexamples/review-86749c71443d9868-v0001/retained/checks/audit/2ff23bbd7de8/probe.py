"""Bounded audit: profile/frame covariance and a crossed lawful challenge."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
ROOT=WORK/'repo'
sys.path.insert(0,str(ROOT/'shared/runtime'))
# The sparse wrapper does not stage the legacy scripts package; expose its
# existing authoritative parser module under the import name rule_wrap expects.
import types
parser_source=ROOT/'shared/tools/comment_solutions.py'
parser_spec=importlib.util.spec_from_file_location('scripts.comment_solutions',parser_source)
parser_module=importlib.util.module_from_spec(parser_spec)
legacy_package=types.ModuleType('scripts');legacy_package.__path__=[str(parser_source.parent)]
sys.modules['scripts']=legacy_package
sys.modules['scripts.comment_solutions']=parser_module
parser_spec.loader.exec_module(parser_module)
from puzzle_generators.runner import wrap_rule
from arc_repl.racket_bridge import RacketBridge
import arc_repl.racket_bridge as bridge_module
TASK='2ff23bbd7de8'
source=ROOT/'generators'/TASK/'generator.py'
source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_sha=='33f9e73f9ef368d0265261541534d2d7fddc4fe889e697c99c2b657519da904f'
spec=importlib.util.spec_from_file_location('audit_selected_generator',source)
gen=importlib.util.module_from_spec(spec);sys.modules[spec.name]=gen;spec.loader.exec_module(gen)
rows=[]
for line in (ROOT/'shared/data/canonical/puzzles.jsonl').open():
 row=json.loads(line)
 if row.get('task_id')==TASK: rows.append(row)
assert len(rows)==1
row=rows[0];program=row['program_solution']; pairs=row['train']+[row['test']]
for pair in pairs:
 assert gen.self_check(pair['input'])==[]
 assert gen.rule_mirror(pair['input'])==pair['output']

# Rival is deliberately identical on the entire generated support: orientation 0
# never co-occurs with radius-four distractors, because both depend on index.
def conditional_radius_rival(grid):
 info,errors=gen._analyse(grid)
 assert not errors
 return gen._rival_ignore_radius(grid) if info['orientation']==0 else gen.rule_mirror(grid)

support=[]; lessons=[]; failures=[]
for difficulty in ['easy','medium','hard']:
 for seed in range(8):
  scenes=[]
  for index in range(12):
   grid=gen.generate(seed,index,difficulty=difficulty)
   assert not gen.self_check(grid)
   info,_=gen._analyse(grid)
   assert 1 in info['qcounts']
   assert conditional_radius_rival(grid)==gen.rule_mirror(grid)
   support.append({'seed':seed,'sample_index':index,'difficulty':difficulty,'orientation':info['orientation'],'profile':gen.schedule_profile(seed,index,difficulty),'far_count':info['far_count']})
   scenes.append({'input':grid,'output':gen.rule_mirror(grid)})
  for start in range(8):
   errors=gen.lesson_identifiable(scenes[start:start+4],scenes[start+4])
   lessons.append({'seed':seed,'difficulty':difficulty,'start':start,'errors':errors})
   if errors: failures.append({'seed':seed,'difficulty':difficulty,'start':start,'errors':errors,'demos':scenes[start:start+4],'query':scenes[start+4]})

# Independent construction crosses all eight frames with all four distractor
# profiles, without calling generator placement/allocation helpers.
bases=[((1,0),(0,1)),((1,0),(0,-1)),((-1,0),(0,1)),((-1,0),(0,-1)),((0,1),(1,0)),((0,1),(-1,0)),((0,-1),(1,0)),((0,-1),(-1,0))]
counts=[2,3,4,5];signs=[(1,1),(-1,1),(-1,-1),(1,-1)]
challenges=[]
for orientation,(vx,vy) in enumerate(bases):
 for profile in range(4):
  grid=[[0]*11 for _ in range(11)]
  def place(u,v,color):
   r=5+u*vx[0]+v*vy[0];c=5+u*vx[1]+v*vy[1]
   assert grid[r][c]==0
   grid[r][c]=color
  place(0,0,2);place(1,0,3);place(0,1,4)
  for (su,sv),count in zip(signs,counts):
   for au,av in [(a,b) for a in range(1,4) for b in range(1,4)][:count]: place(su*au,sv*av,8)
  if profile in [1,3]: place(-2,0,8);place(0,-2,8)
  if profile in [2,3]: place(4,1,8);place(-4,-1,8)
  assert not gen.self_check(grid)
  challenges.append({'orientation':orientation,'profile':profile,'input':grid,'expected':[counts]})
with RacketBridge() as bridge:
 bridge.eval_text('(define audit-reference '+wrap_rule(program)+')')
 for challenge in challenges:
  bridge.define_grid('audit-input',challenge['input'])
  output=bridge.eval_text('(audit-reference audit-input)')
  assert output==challenge['expected']
  assert output==gen.rule_mirror(challenge['input'])
  challenge['racket_output']=output
  challenge['conditional_rival_output']=conditional_radius_rival(challenge['input'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_sha
bridge_path=Path(bridge_module.__file__)
witness=next(c for c in challenges if c['orientation']==0 and c['profile']==2)
result={'schema':'bounded-independent-generator-audit-v1','task_id':TASK,'source_sha256':source_sha,
        'rule_sha256':hashlib.sha256(program.encode()).hexdigest(),'canonical_pairs_checked':len(pairs),
        'generated_scenes_checked':len(support),'four_demo_windows_checked':len(lessons),
        'lesson_failures':len(failures),'native_racket_challenges':len(challenges),'native_label_mismatches':0,
        'conditional_rival_generated_disagreements':0,'conditional_rival_crossed_challenge_disagrees':witness['racket_output']!=witness['conditional_rival_output'],
        'observed_orientation_profile_pairs':sorted({(r['orientation'],r['profile']) for r in support}),
        'bridge_sha256':hashlib.sha256(bridge_path.read_bytes()).hexdigest(),
        'prelude_sha256':hashlib.sha256((bridge_path.parent/'racket_prelude/arc-prelude.rkt').read_bytes()).hexdigest()}
for name,value in [('receipt.json',result),('support.json',support),('witness.json',witness),('crossed-challenges.json',challenges),('lesson-failures.json',failures)]:
 (HERE/name).write_text(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps(result,sort_keys=True))
