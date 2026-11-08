from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID="0af9951eba63"
ROOT=Path.cwd()
GEN,SOURCE,SOURCE_SHA=load_selected_generator(TASK_ID,root=ROOT)


def panels(grid):
    h=len(grid); w=len(grid[0]); pw=(w-2)//3
    a=[row[:pw] for row in grid]
    b=[row[pw+1:2*pw+1] for row in grid]
    c=[row[2*pw+2:] for row in grid]
    return a,b,c


def conflict_facts(grid):
    a,b,c=panels(grid); vals=defaultdict(set); positions=defaultdict(list)
    for r,row in enumerate(a):
        for col,v in enumerate(row):
            if v:
                vals[v].add(b[r][col]); positions[v].append((r,col,b[r][col]))
    return {"has_conflict":any(len(x)>1 for x in vals.values()),"targets":{str(k):sorted(v) for k,v in vals.items()},"positions":{str(k):v for k,v in positions.items()},"c_nonzero":sorted({v for row in c for v in row if v})}


def connected8(cells):
    cells=set(cells)
    if not cells:return True
    seen={next(iter(cells))}; q=deque(seen)
    while q:
        r,c=q.popleft()
        for dr in (-1,0,1):
            for dc in (-1,0,1):
                if dr==dc==0:continue
                p=(r+dr,c+dc)
                if p in cells and p not in seen: seen.add(p); q.append(p)
    return seen==cells

conflict_failure=None
errors=[]
for seed in range(2000):
    try:
        g=GEN.generate(seed,0,difficulty="easy",panel_h=3,panel_w=3,n_pairs=5,texture="conflict")
    except Exception as exc:
        errors.append({"seed":seed,"type":type(exc).__name__,"message":str(exc)})
        continue
    facts=conflict_facts(g)
    if not facts["has_conflict"]:
        conflict_failure={"seed":seed,"sample_index":0,"overrides":{"difficulty":"easy","panel_h":3,"panel_w":3,"n_pairs":5,"texture":"conflict"},"input":g,"facts":facts,"self_check":GEN.self_check(g)}
        break

shape_failure=None
for seed in range(500):
    g=GEN.generate(seed,1,difficulty="medium",texture="plain")
    a,b,c=panels(g)
    by=defaultdict(list)
    for r,row in enumerate(a):
        for col,v in enumerate(row):
            if v: by[v].append((r,col))
    bad={str(color):cells for color,cells in by.items() if len(cells)>1 and not connected8(cells)}
    if bad:
        shape_failure={"seed":seed,"sample_index":1,"overrides":{"difficulty":"medium","texture":"plain"},"input":g,"disconnected_source_colors":bad,"self_check":GEN.self_check(g)}
        break

false_accept=[[0]*14 for _ in range(4)]
for r in range(4):
    false_accept[r][1]=5
    false_accept[r][12]=5
false_accept[0][0]=2
false_accept[0][2]=7
false_accept[0][13]=2

report={
 "schema":"audit-probe-v1","task_id":TASK_ID,
 "generator_path":str(SOURCE.relative_to(ROOT)),"generator_sha256":SOURCE_SHA,
 "conflict_search":{"seeds":"0..1999 until first failure","failure":conflict_failure,"generation_errors":errors[:5]},
 "shape_search":{"seeds":"0..499 until first disconnected multi-cell source","failure":shape_failure},
 "self_check_false_accept":{"input":false_accept,"self_check":GEN.self_check(false_accept),"reason":"two full-height separators are at columns 1 and 12, not equal-panel boundaries 4 and 9"},
 "command":"python3 review.py run python3 ../checks/audit/0af9951eba63/probe.py","cwd":str(ROOT),
}
Path("../checks/audit/0af9951eba63/probe.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
Path("../checks/audit/0af9951eba63/unequal-panels-input.json").write_text(json.dumps(false_accept)+"\n")
print(json.dumps({"generator_sha256":SOURCE_SHA,"conflict_failure":conflict_failure,"shape_failure":shape_failure,"self_check_false_accept":report["self_check_false_accept"]},indent=2,sort_keys=True))
