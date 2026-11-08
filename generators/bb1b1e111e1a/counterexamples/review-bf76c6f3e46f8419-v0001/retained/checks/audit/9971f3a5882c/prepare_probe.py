from pathlib import Path
import copy, hashlib, json
from reviewer_support import canonical_pairs, load_selected_generator

TASK='9971f3a5882c'
ROOT=Path.cwd()
OUT=ROOT.parent/'checks/audit'/TASK
EXPECTED='ac6f4a04bb8a7947d942a3eb5232eafd065956f1d1226a3190e727f75ac84e14'
gen,source,sha=load_selected_generator(TASK,root=ROOT)
assert sha==EXPECTED, (sha,EXPECTED)
(OUT/'selected_generator.py').write_bytes(source.read_bytes())
canon=canonical_pairs(TASK,root=ROOT,labeled_only=True)
canon_checks=[{'variant':p['variant'],'split':p['split'],'pair_index':p['pair_index'],
 'self_check':gen.self_check(p['input']),
 'mirror_matches_stored_canonical':gen.solve_python(p['input'])==p['output'],
 'rival_matches_stored_canonical':{name:f(copy.deepcopy(p['input']))==p['output'] for name,f in gen.LESSON_COMPETITORS.items()}} for p in canon]

def describe(name,grid,replay):
 return {'name':name,'replay':replay,'input':grid,'self_check':gen.self_check(grid),
  'strict_canonical_like':gen.strict_canonical_like(grid),'observed':gen.observe_overrides(grid),
  'analysis':gen._analyze_lattice(grid),
  'python_mirror_output':gen.solve_python(copy.deepcopy(grid)),
  'rival_outputs':{key:fn(copy.deepcopy(grid)) for key,fn in gen.LESSON_COMPETITORS.items()},
  'semantic_witnesses':{key:fn(copy.deepcopy(grid)) for key,fn in gen.SEMANTIC_WITNESSES.items()}}

cases=[]
for index in range(4):
 overrides={'marker_profile':'left_bottom'}
 grid=gen.generate(9971,index,difficulty='medium',**overrides)
 cases.append(describe(f'equivalent_lesson_pair_{index}',grid,{'seed':9971,'sample_index':index,'difficulty':'medium','overrides':overrides,'mutation':None}))
overrides={'canvas_profile':'c11x15','lattice_profile':'frame3x3','marker_profile':'double_left_bottom'}
grid=gen.generate(9971,7,difficulty='medium',**overrides)
original=copy.deepcopy(grid)
analysis=gen._analyze_lattice(grid)
r0,r1,c0,c1=analysis['bbox']
left=[(r,c) for r,c in analysis['marks'] if c<c0]
near_col=max(c for _,c in left)
for r,c in left:grid[r][c]=0
new=[(r0,near_col),(r1,near_col)]
for r,c in new:grid[r][c]=6
case=describe('tied_longitudinal_marker_distances',grid,{'seed':9971,'sample_index':7,'difficulty':'medium','overrides':overrides,'mutation':{'remove_markers':left,'add_markers':new,'meaning':'Put the two left markers at distinct rows but the same column.'}})
case['original_generated_input']=original
cases.append(case)
report={'schema':'9971-source-bound-audit-probe-v1','task_id':TASK,'source_sha256':sha,'declared_rule_hash':gen.RULE_HASH,'canonical_pairs':canon_checks,'cases':cases,'labels':'python_mirror_and_declared_rivals_only_until_racket_assessment'}
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'input.json').write_text(json.dumps({'inputs':[c['input'] for c in cases]})+'\n')
print(json.dumps({'source_sha256':sha,'canonical_pairs':len(canon),'all_canonical_inputs_accepted':all(not x['self_check'] for x in canon_checks),'all_canonical_mirrors_match':all(x['mirror_matches_stored_canonical'] for x in canon_checks),'all_declared_rivals_fit_all_canonical':all(all(x['rival_matches_stored_canonical'].values()) for x in canon_checks),'cases':len(cases),'all_probe_inputs_accepted':all(not x['self_check'] for x in cases),'tie_witness_fires':cases[-1]['semantic_witnesses']['multiple_same_side_markers']},indent=2))
