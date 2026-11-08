#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from collections import deque
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK='561ebfa521f0'
root=find_root(__file__)
gen,path,sha=load_selected_generator(TASK,root=root)
grid=[
 [5,5,5,5,5,5,5,5,5],
 [5,2,0,5,0,4,0,0,5],
 [5,0,0,5,0,0,0,0,5],
 [5,5,5,5,5,5,5,5,5],
 [5,0,0,0,0,0,0,3,5],
 [5,0,0,0,0,0,0,0,5],
 [5,5,5,5,5,5,5,5,5],
]

def position(color):
 return next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color)
def reachable(start):
 q=deque([start]); seen={start}
 while q:
  r,c=q.popleft()
  for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
   p=(r+dr,c+dc)
   if 0<=p[0]<len(grid) and 0<=p[1]<len(grid[0]) and grid[p[0]][p[1]]!=5 and p not in seen:
    seen.add(p); q.append(p)
 return seen
positions={str(c):position(c) for c in (2,4,3)}
reach=reachable(positions['2'])
report={
 'task_id':TASK,
 'generator_path':str(path.relative_to(root)),
 'generator_sha256':sha,
 'generator_version':gen.VERSION,
 'input':grid,
 'input_sha256':hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest(),
 'self_check':gen.self_check(grid),
 'declared_invariant':'all 3 markers reachable from each other through non-wall cells',
 'marker_positions':positions,
 'reachable_from_2':sorted([list(p) for p in reach]),
 'marker_4_reachable_from_2':positions['4'] in reach,
 'marker_3_reachable_from_2':positions['3'] in reach,
 'finding':'self_check accepts a grid that violates the declared marker-reachability invariant',
}
here=Path(__file__).resolve().parent
(here/'input.json').write_text(json.dumps(grid,indent=2)+'\n')
(here/'counterexample.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:report[k] for k in ('generator_sha256','self_check','marker_4_reachable_from_2','marker_3_reachable_from_2')},indent=2))
