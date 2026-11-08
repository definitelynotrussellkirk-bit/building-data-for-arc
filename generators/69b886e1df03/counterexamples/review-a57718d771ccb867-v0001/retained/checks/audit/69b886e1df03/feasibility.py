"""Exact rejected-control repro and independent feasible packing witness."""
import importlib.util,json
from pathlib import Path
from collections import deque
OUT=Path('checks/audit/69b886e1df03')
source=Path('repo/generators/69b886e1df03/generator.py')
spec=importlib.util.spec_from_file_location('target',source)
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
grid=[[2,2,0,3,3],[2,0,4,0,3],[0,5,0,6,0],[0,5,5,0,7]]
seen=set();components=[]
for r,row in enumerate(grid):
 for c,color in enumerate(row):
  if not color or (r,c) in seen:continue
  q=deque([(r,c)]);seen.add((r,c));cells=[]
  while q:
   x,y=q.popleft();cells.append((x,y))
   for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
    p=x+dx,y+dy
    if 0<=p[0]<4 and 0<=p[1]<5 and p not in seen and grid[p[0]][p[1]]==color:
     q.append(p);seen.add(p)
  components.append((color,cells))
expected=[[0]*5 for _ in range(4)]
boxes=[]
for color,cells in components:
 rs,cs=zip(*cells);box=min(rs),min(cs),max(rs),max(cs);boxes.append(box)
 for r in range(box[0],box[2]+1):
  for c in range(box[1],box[3]+1):expected[r][c]=color
controls=dict(grid_h=4,grid_w=5,n_objects=6)
report=dict(generated_call=dict(seed=0,sample_index=0,difficulty='easy',overrides=controls),feasible_input=grid,independent_four_connected_output=expected,independent_identity_rival_output=grid,validator_errors=gen.self_check(grid),observed_controls=gen.observe_overrides(grid),independent_components=[dict(color=col,cells=cells,bbox=box) for (col,cells),box in zip(components,boxes)],zero_count=sum(v==0 for row in grid for v in row),modal_nonzero_count=3)
try:
 report['generated_grid']=gen.generate(0,0,difficulty='easy',**controls)
except Exception as e:
 report['generation_exception']=dict(type=type(e).__name__,message=str(e))
(OUT/'feasible-input.json').write_text(json.dumps(grid)+'\n')
(OUT/'feasibility.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
assert report['validator_errors']==[]
assert report['observed_controls']==controls
assert report['generation_exception']['type']=='ValueError'
