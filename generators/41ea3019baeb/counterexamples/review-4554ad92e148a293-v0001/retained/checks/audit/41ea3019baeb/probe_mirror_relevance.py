from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "41ea3019baeb"
ROOT = Path.cwd()
GEN, SOURCE, SHA = load_selected_generator(TASK, root=ROOT)
OUT = ROOT.parent / "checks" / "audit" / TASK
DIRECTIONS = ((-1,0),(1,0),(0,-1),(0,1))

def turn(v, dr, dc):
    if v == 6:
        return {(0,1):(-1,0),(0,-1):(1,0),(-1,0):(0,1),(1,0):(0,-1)}[(dr,dc)]
    if v == 7:
        return {(0,1):(1,0),(0,-1):(-1,0),(-1,0):(0,-1),(1,0):(0,1)}[(dr,dc)]
    return dr, dc

def interactions(grid, start):
    h,w=len(grid),len(grid[0]); r,c=start; dr,dc=0,1; hits=[]; seen=set()
    for _ in range(h*w*8):
        state=(r,c,dr,dc)
        if state in seen: break
        seen.add(state)
        nr,nc=r+dr,c+dc
        if not (0<=nr<h and 0<=nc<w): break
        v=grid[nr][nc]
        if v in (5,6,7): hits.append((nr,nc,v))
        if v==5 or (v!=0 and v not in (6,7)): break
        dr,dc=turn(v,dr,dc); r,c=nr,nc
    return hits

def straight_rival(grid):
    out=[row[:] for row in grid]; h=len(grid); w=len(grid[0])
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v != 2: continue
            cc=c+1
            while cc<w and grid[r][cc]==0:
                out[r][cc]=8; cc+=1
    return out

bands={}
all_rows=[]
for bi,band in enumerate(("easy","medium","hard")):
    no_touch=0; two_plus=0; passed=0
    for i in range(100):
        seed=50000+10000*bi+i
        grid=GEN.generate(seed,i,difficulty=band)
        errs=GEN.self_check(grid,difficulty=band)
        passed += int(not errs)
        emitters=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==2]
        counts=[len(interactions(grid,e)) for e in emitters]
        no_touch += int(sum(counts)==0)
        two_plus += int(any(count>=2 for count in counts))
        all_rows.append({"band":band,"seed":seed,"sample_index":i,"mirror_hits":counts,"self_check":errs})
    bands[band]={"samples":100,"self_check_pass":passed,"no_mirror_touched":no_touch,"path_with_two_plus_mirrors":two_plus}

lesson=[GEN.generate(1000,i,difficulty="easy") for i in range(4)]
canonical=canonical_pairs(TASK,root=ROOT,labeled_only=True)[0]["input"]
(OUT/"lesson-inputs.json").write_text(json.dumps({"inputs":lesson},indent=2)+"\n")
(OUT/"lesson-straight-rival.json").write_text(json.dumps({"outputs":[straight_rival(g) for g in lesson]},indent=2)+"\n")
(OUT/"canonical-input.json").write_text(json.dumps({"input":canonical},indent=2)+"\n")
(OUT/"canonical-straight-rival.json").write_text(json.dumps({"output":straight_rival(canonical)},indent=2)+"\n")
report={"schema":"audit-mirror-relevance-v1","task_id":TASK,"generator_sha256":SHA,"bands":bands,"rows":all_rows,
        "lesson_seed":1000,"lesson_sample_indices":[0,1,2,3],"lesson_self_checks":[GEN.self_check(g,difficulty="easy") for g in lesson]}
(OUT/"mirror-probe.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps({"task_id":TASK,"generator_sha256":SHA,"bands":bands},indent=2))
