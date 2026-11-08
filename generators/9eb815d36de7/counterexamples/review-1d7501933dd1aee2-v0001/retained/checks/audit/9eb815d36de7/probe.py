from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from pathlib import Path

from reviewer_support import load_selected_generator

TASK_ID = "9eb815d36de7"
ROOT = Path.cwd()
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)


def norm(cells):
    r0 = min(r for r, _ in cells); c0 = min(c for _, c in cells)
    return tuple(sorted((r-r0, c-c0) for r,c in cells))


def components(grid, color=3):
    cells={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color}
    out=[]
    while cells:
        start=next(iter(cells)); cells.remove(start); q=deque([start]); comp={start}
        while q:
            r,c=q.popleft()
            for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                p=(r+dr,c+dc)
                if p in cells:
                    cells.remove(p); comp.add(p); q.append(p)
        out.append(comp)
    return out

expected = {
    "missing_top_left": norm({(0,1),(1,0),(1,1)}),
    "missing_top_right": norm({(0,0),(1,0),(1,1)}),
    "missing_bottom_left": norm({(0,0),(0,1),(1,1)}),
    "missing_bottom_right": norm({(0,0),(0,1),(1,0)}),
}
declared=[norm(set(shape)) for shape in GEN.L_SHAPES]
orientation_counts=Counter()
unknown=[]
for seed in range(100):
    for sample_index in range(8):
        grid=GEN.generate(seed,sample_index,difficulty="medium")
        for comp in components(grid):
            pattern=norm(comp)
            names=[name for name,value in expected.items() if value==pattern]
            if names: orientation_counts[names[0]] += 1
            else: unknown.append({"seed":seed,"sample_index":sample_index,"cells":sorted(comp)})

base_args=dict(seed=12345,sample_index=6,difficulty="medium")
override_pairs={
    "palette_kind": ("warm","cool"),
    "texture": ("warm","cool"),
}
override_results={}
for axis,(a,b) in override_pairs.items():
    ga=GEN.generate(**base_args, **{axis:a})
    gb=GEN.generate(**base_args, **{axis:b})
    override_results[axis]={
        "value_a":a,"value_b":b,"identical":ga==gb,
        "sha_a":hashlib.sha256(json.dumps(ga,separators=(",",":")).encode()).hexdigest(),
        "sha_b":hashlib.sha256(json.dumps(gb,separators=(",",":")).encode()).hexdigest(),
    }

false_accept=[[0]*7 for _ in range(5)]
false_accept[0][0]=2
for c in (2,3,4): false_accept[2][c]=3

report={
    "schema":"audit-probe-v1",
    "task_id":TASK_ID,
    "generator_path":str(SOURCE.relative_to(ROOT)),
    "generator_sha256":SOURCE_SHA,
    "declared_l_shapes_raw":GEN.L_SHAPES,
    "declared_normalized_shapes":[list(map(list,p)) for p in declared],
    "declared_shape_entries":len(declared),
    "declared_unique_orientations":len(set(declared)),
    "missing_declared_orientations":[name for name,p in expected.items() if p not in set(declared)],
    "sample_range":{"seeds":"0..99","sample_indices":"0..7","difficulty":"medium"},
    "generated_orientation_counts":dict(orientation_counts),
    "unknown_components":unknown,
    "override_pair_results":override_results,
    "self_check_false_accept":{
        "input":false_accept,
        "self_check":GEN.self_check(false_accept),
        "reason":"three color-3 cells form a straight line, not an L-triomino",
    },
    "command":"python3 review.py run python3 ../checks/audit/9eb815d36de7/probe.py",
    "cwd":str(ROOT),
}
Path("../checks/audit/9eb815d36de7/probe.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
Path("../checks/audit/9eb815d36de7/non-l-input.json").write_text(json.dumps(false_accept)+"\n")
print(json.dumps({k:report[k] for k in ("generator_sha256","declared_unique_orientations","missing_declared_orientations","generated_orientation_counts","override_pair_results","self_check_false_accept")},indent=2,sort_keys=True))
