"""Findings-only public-domain probe; no solve artifacts or external data."""
import hashlib, importlib.util, json
from pathlib import Path
from collections import deque
from reviewer_support import find_root, canonical_path, canonical_pairs
TASK='69b886e1df03'
OUT=Path('checks/audit')/TASK
source=Path('repo/generators')/TASK/'generator.py'
root=find_root(source)
spec=importlib.util.spec_from_file_location('audit_generator',source)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
row=next(json.loads(line) for line in canonical_path(root).read_text().splitlines() if json.loads(line).get('task_id')==TASK)
rule=row['program_solution']

def groups(grid,diagonal=False):
 seen=set(); result=[]; steps=[(1,0),(-1,0),(0,1),(0,-1)]
 if diagonal: steps += [(1,1),(1,-1),(-1,1),(-1,-1)]
 for r in range(len(grid)):
  for c in range(len(grid[0])):
   color=grid[r][c]
   if not color or (r,c) in seen: continue
   seen.add((r,c)); q=deque([(r,c)]); cells=[]
   while q:
    x,y=q.popleft(); cells.append((x,y))
    for dx,dy in steps:
     p=(x+dx,y+dy)
     if 0<=p[0]<len(grid) and 0<=p[1]<len(grid[0]) and p not in seen and grid[p[0]][p[1]]==color:
      seen.add(p);q.append(p)
   result.append((color,cells))
 return result

def fill(grid,diagonal=False):
 output=[[0]*len(grid[0]) for _ in grid]
 for color,cells in groups(grid,diagonal):
  rs,cs=zip(*cells)
  for r in range(min(rs),max(rs)+1):
   for c in range(min(cs),max(cs)+1):output[r][c]=color
 return output

input_grid=[[2,2,0,0,3],[0,2,0,0,0],[0,0,2,2,0],[0,0,2,0,0]]
report=dict(task_id=TASK,generator_version=gen.VERSION,generator_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),rule_sha256_raw=hashlib.sha256(rule.encode()).hexdigest(),rule_sha256_normalized=hashlib.sha256(' '.join(rule.split()).encode()).hexdigest(),declared_rule_hash=gen.RULE_HASH,rule_source=rule,input=input_grid,generated=False,seed=None,sample_index=None,overrides=None,validator_errors=gen.self_check(input_grid),independent_four_connected_output=fill(input_grid),independent_eight_connected_output=fill(input_grid,True),domain=dict(dimensions=[4,5],components=len(groups(input_grid)),colors=len({color for color,_ in groups(input_grid)}),zero_cells=sum(v==0 for r in input_grid for v in r),nonzero_color_counts={color:sum(v==color for r in input_grid for v in r) for color in (2,3)},expanding_components=2,identity_components=1,bboxes_pairwise_disjoint=True,orthogonally_separated=True,diagonal_same_color_contact=True))
pairs=canonical_pairs(TASK,root=root)
report['canonical_eight_connected_fit']=[fill(p['input'],True)==p['output'] for p in pairs]
report['canonical_validator_errors']=[gen.self_check(p['input']) for p in pairs]
report['default_probe']=dict(cases=0,eight_connected_agreements=0,eight_connected_counterexamples=[],generation_errors=[])
for band in ('easy','medium','hard'):
 for seed in range(20):
  for index in (0,1,2):
   bucket=report['default_probe']; bucket['cases']+=1
   try:
    g=gen.generate(seed,index,difficulty=band)
    if fill(g)==fill(g,True):bucket['eight_connected_agreements']+=1
    else:bucket['eight_connected_counterexamples'].append(dict(seed=seed,sample_index=index,difficulty=band,input=g))
   except Exception as e:bucket['generation_errors'].append(dict(seed=seed,sample_index=index,difficulty=band,error=str(e)))
report['small_controls_probe']=dict(cases=0,errors=[])
for n in range(2,7):
 for seed in range(8):
  for index in (0,1,2):
   bucket=report['small_controls_probe']; bucket['cases']+=1
   ctl=dict(grid_h=4,grid_w=5,n_objects=n)
   try:
    g=gen.generate(seed,index,difficulty='easy',**ctl)
    if gen.observe_overrides(g)!=ctl:raise AssertionError('dishonest controls')
   except Exception as e:bucket['errors'].append(dict(seed=seed,sample_index=index,difficulty='easy',overrides=ctl,exception=type(e).__name__,error=str(e)))
(OUT/'input.json').write_text(json.dumps(input_grid)+'\n')
(OUT/'finding.json').write_text(json.dumps(report,indent=2)+'\n')
summary={k:report[k] for k in ('generator_sha256','rule_sha256_normalized','validator_errors','canonical_eight_connected_fit','default_probe','small_controls_probe')}
print(json.dumps(summary))
