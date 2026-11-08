#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK='109a03554ed3'
gen, source, sha = load_selected_generator(TASK, root=find_root(__file__))

def analysis(grid):
    red=gen._anchored_offsets(grid,2)
    blue=gen._anchored_offsets(grid,1)
    return {
      'red_offsets': sorted(map(list,red)),
      'blue_offsets': sorted(map(list,blue)),
      'overlap_offsets': sorted(map(list,red & blue)),
      'xor_offsets': sorted(map(list,red ^ blue)),
      'union_offsets': sorted(map(list,red | blue)),
    }

def union_rival(grid):
    h,w=len(grid),len(grid[0]); out=[[0]*w for _ in range(h)]
    red=gen._anchored_offsets(grid,2); blue=gen._anchored_offsets(grid,1)
    target=gen._positions(grid,8)[0]
    for dr,dc in red|blue:
        if (dr,dc)!=(0,0):
            r,c=target[0]+dr,target[1]+dc
            if 0<=r<h and 0<=c<w: out[r][c]=3
    return out

found=None
for seed in range(1000):
    for start in range(24):
        grids=[gen.generate(seed,start+i,difficulty='medium') for i in range(5)]
        rows=[analysis(g) for g in grids]
        if all(not r['overlap_offsets'] for r in rows[:4]) and rows[4]['overlap_offsets']:
            found=(seed,start,grids,rows)
            break
    if found: break
if not found:
    raise SystemExit('no witness found')
seed,start,grids,rows=found
payload={
 'schema':'arc-audit-union-survivor-v1',
 'task_id':TASK,
 'generator_path':str(source),
 'generator_sha256':sha,
 'seed':seed,
 'start_sample_index':start,
 'difficulty':'medium',
 'examples_needed':gen.EXAMPLES_NEEDED,
 'pairs':[],
}
for i,(grid,row) in enumerate(zip(grids,rows)):
    payload['pairs'].append({
      'role':'demo' if i<4 else 'query',
      'sample_index':start+i,
      'input':grid,
      'self_check':gen.self_check(grid),
      'analysis':row,
      'union_rival_output':union_rival(grid),
    })
out=Path('../checks/audit/109a03554ed3/union_survivor_source.json')
out.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
Path('../checks/audit/109a03554ed3/inputs.json').write_text(json.dumps(grids)+'\n')
print(json.dumps({'seed':seed,'start':start,'sha':sha,'overlaps':[len(r['overlap_offsets']) for r in rows]}))
