from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
AUDIT = Path(__file__).resolve().parent


def load(task):
    p = REPO / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", p)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(m)
    return m, p


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def read_json(p): return json.loads(p.read_text())


def objects(grid, banned=()):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r0 in range(h):
        for c0 in range(w):
            color=grid[r0][c0]
            if color==0 or color in banned or (r0,c0) in seen: continue
            q=deque([(r0,c0)]); seen.add((r0,c0)); cells=[]
            while q:
                r,c=q.popleft(); cells.append((r,c))
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr,nc=r+dr,c+dc
                    if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
                        seen.add((nr,nc)); q.append((nr,nc))
            out.append({"color":color,"cells":sorted(cells)})
    return out


def blank_like(g): return [[0]*len(g[0]) for _ in g]


def rival_1d_top_left(grid):
    candidates=objects(grid,banned=(1,))
    chosen=min(candidates,key=lambda o:min(o["cells"]))
    marker=min(o["cells"] for o in objects(grid) if o["color"]==1)[0]
    rmin=min(r for r,c in chosen["cells"]); rmax=max(r for r,c in chosen["cells"])
    prof=[sum(r==rr for r,c in chosen["cells"]) for rr in range(rmin,rmax+1)]
    out=blank_like(grid)
    mr,mc=marker
    for dr,count in enumerate(prof):
        for dc in range(count): out[mr+dr][mc+dc]=8
    return out


def rival_9c_second_largest(grid):
    ranked=sorted(objects(grid),key=lambda o:(len(o["cells"]), min(o["cells"])))
    chosen=ranked[-2]
    out=blank_like(grid)
    for r,c in chosen["cells"]: out[r][c]=chosen["color"]
    return out


def make_1d():
    task="1d8a1c70332a"; m,p=load(task); d=AUDIT/task
    inp=read_json(d/"input.json"); racket=read_json(d/"racket.json")
    rival=rival_1d_top_left(inp); actual=racket["results"][0]["output"]
    report={
      "schema":"arcpuzzles-audit-counterexample-v1",
      "task_id":task,
      "finding":"validator_accepts_multiple_anchors_while_generation_never_teaches_largest_selection",
      "generator_sha256":sha(p),
      "rule_hash":racket["executed_rule_hash"],
      "input":inp,
      "target_self_check":m.self_check(inp),
      "documented_generator_domain":"outside: INVARIANTS says exactly one non-color-1 object",
      "validator_domain":"inside: self_check returns no errors",
      "actual_racket_output":actual,
      "rival_name":"top_left_non_color_1_object",
      "rival_output":rival,
      "rival_disagrees":rival!=actual,
      "apply_evidence":"checks/audit/1d8a1c70332a/racket.json",
      "command":racket["command"],
      "cwd":"repo",
    }
    (d/"rival.json").write_text(json.dumps(rival,indent=2)+"\n")
    (d/"counterexample.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report


def make_9c():
    task="9c69eb63c11a"; m,p=load(task); d=AUDIT/task
    inp=read_json(d/"input.json"); racket=read_json(d/"racket.json")
    rival=rival_9c_second_largest(inp); actual=racket["results"][0]["output"]
    report={
      "schema":"arcpuzzles-audit-counterexample-v1",
      "task_id":task,
      "finding":"advertised_five_blob_domain_refutes_second_largest_shortcut_but_generator_only_emits_three",
      "generator_sha256":sha(p),
      "rule_hash":racket["executed_rule_hash"],
      "input":inp,
      "component_areas":[1,2,3,4,5],
      "target_self_check":m.self_check(inp),
      "documented_generator_domain":"inside AXES: n_blobs valid 3..5, palette_size/n_distinct_colors valid 3..5; outside current self_check hard-code exactly 3",
      "actual_racket_output":actual,
      "rival_name":"keep_second_largest_blob",
      "rival_output":rival,
      "rival_disagrees":rival!=actual,
      "canonical_fit_reason":"With exactly three distinct-size blobs, the median is the second-largest; all canonical pairs and all ordinary generated inputs have exactly three blobs.",
      "apply_evidence":"checks/audit/9c69eb63c11a/racket.json",
      "command":racket["command"],
      "cwd":"repo",
    }
    (d/"rival.json").write_text(json.dumps(rival,indent=2)+"\n")
    (d/"counterexample.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    return report

print(json.dumps({"counterexamples":[make_1d(),make_9c()]},indent=2,sort_keys=True))
