from __future__ import annotations
from pathlib import Path
from collections import deque
import hashlib, json
from reviewer_support import load_selected_generator

TASK='483682b75e12'
EXPECTED='189fbe70222e7cb05feeb7114eb0ad2a3f4f557e532cf23e3ea0a8c686979f7e'
module,path,sha=load_selected_generator(TASK)
if sha != EXPECTED:
    raise ValueError((sha,EXPECTED,path))

def components(grid):
    h,w=len(grid),len(grid[0])
    fg={(r,c) for r in range(h) for c in range(w) if grid[r][c] not in (7,8)}
    out=[]; seen=set()
    for start in sorted(fg):
        if start in seen: continue
        q=[start]; seen.add(start); cells=[]
        while q:
            r,c=q.pop(); cells.append((r,c))
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                n=(r+dr,c+dc)
                if n in fg and n not in seen:
                    seen.add(n); q.append(n)
        out.append(tuple(sorted(cells)))
    return out

def bbox_area_rival(grid):
    h,w=len(grid),len(grid[0])
    out=[[8 if grid[r][c]==8 else 7 for c in range(w)] for r in range(h)]
    for cells in components(grid):
        rs=[r for r,_ in cells]; cs=[c for _,c in cells]
        shift=(max(rs)-min(rs)+1)*(max(cs)-min(cs)+1)
        for r,c in cells:
            if r-shift >= 0:
                out[r-shift][c]=grid[r][c]
    return out

checked=0
found=None
for seed in range(512):
    inputs=[module.generate(seed,i) for i in range(4)]
    if any(module.self_check(g) for g in inputs):
        continue
    targets=[module.rule_mirror(g) for g in inputs]
    rivals=[bbox_area_rival(g) for g in inputs]
    checked += 1
    if targets[:3] == rivals[:3] and targets[3] != rivals[3]:
        found={
            'schema':'arcpuzzles-peer-adversarial-witness-v1',
            'task_id':TASK,
            'source_path':str(path.relative_to(Path.cwd())),
            'source_sha256':sha,
            'rival':'shift each component upward by bounding-box area instead of cell count',
            'seed':seed,
            'sample_indices':[0,1,2,3],
            'demonstrations':[
                {'input':inputs[i],'canonical_output':targets[i],'rival_output':rivals[i]}
                for i in range(3)
            ],
            'query':{
                'input':inputs[3],
                'canonical_output':targets[3],
                'rival_output':rivals[3],
                'differing_cells':[
                    [r,c,targets[3][r][c],rivals[3][r][c]]
                    for r in range(len(inputs[3])) for c in range(len(inputs[3][0]))
                    if targets[3][r][c] != rivals[3][r][c]
                ],
            },
            'scope':f'first witness in seeds 0..511 using consecutive sample indices 0..3; checked {checked} valid lessons',
            'racket_status':'pending',
        }
        break
out=Path('../checks/peers/483682b75e12/search-result.json')
out.write_text(json.dumps({'checked':checked,'found':found},indent=2,sort_keys=True)+'\n')
print(json.dumps({'checked':checked,'found_seed':None if found is None else found['seed'],'differences':0 if found is None else len(found['query']['differing_cells'])},sort_keys=True))
