"""Focused findings-only audit; writes only beside this script."""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared/runtime"))
from reviewer_support import canonical_pairs, load_selected_generator
from puzzle_generators import base

TASK_ID = "d9f6e69efb45"
EXPECTED_SOURCE = "46f76938a6c2e32a047f5e3db58df3c927802f7831d42210220c713717363f49"

def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

def frames(grid):
    """Independent 4-connected gray-frame observer, permitting 3-cell sides."""
    h, w = len(grid), len(grid[0])
    seen, found = set(), []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5 or (r,c) in seen:
                continue
            stack, cells = [(r,c)], set()
            seen.add((r,c))
            while stack:
                rr,cc = stack.pop()
                cells.add((rr,cc))
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    p=(rr+dr,cc+dc)
                    if 0<=p[0]<h and 0<=p[1]<w and p not in seen and grid[p[0]][p[1]]==5:
                        seen.add(p); stack.append(p)
            r1,r2=min(r for r,c in cells),max(r for r,c in cells)
            c1,c2=min(c for r,c in cells),max(c for r,c in cells)
            if r2-r1<2 or c2-c1<2:
                continue
            perimeter={(rr,cc) for rr in range(r1,r2+1) for cc in range(c1,c2+1)
                       if rr in (r1,r2) or cc in (c1,c2)}
            if cells==perimeter:
                found.append((r1,c1,r2,c2))
    return found

def restricted_frame_rival(grid):
    """Fill seeded frames only when BOTH outer side lengths are at least 4."""
    out=[row[:] for row in grid]
    for r1,c1,r2,c2 in frames(grid):
        if min(r2-r1+1,c2-c1+1)<4:
            continue
        colors={grid[r][c] for r in range(r1+1,r2) for c in range(c1+1,c2)}-{0,5}
        if len(colors)==1:
            color=next(iter(colors))
            for r in range(r1+1,r2):
                for c in range(c1+1,c2):
                    if out[r][c]==0:out[r][c]=color
    return out

m, source_path, source_hash=load_selected_generator(TASK_ID,root=REPO)
assert source_hash==EXPECTED_SOURCE, (source_hash,EXPECTED_SOURCE)
overrides={"grid_h":8,"grid_w":11,"n_frames":2}
captured=[]
base.set_ctx_observer(captured.append)
try:
    generated=m.generate(0,0,difficulty="medium",**overrides)
finally:
    base.set_ctx_observer(None)
ctx=captured[-1]
assert ctx.recorded_draws()["n_frames"]==ctx.overrides_used()["n_frames"]==2
assert len(frames(generated))==1
assert m.self_check(generated,difficulty="medium")==[]

canonical=canonical_pairs(TASK_ID,root=REPO)
train=[p for p in canonical if p["split"]=="train"]
assert len(canonical)==3 and len(train)==2
canonical_validation=[{"variant":p["variant"],"split":p["split"],"pair_index":p["pair_index"],
                       "shape":[len(p["input"]),len(p["input"][0])],
                       "frame_bounds":frames(p["input"]),"self_check":m.self_check(p["input"])}
                      for p in canonical]
assert sum(bool(p["self_check"]) for p in canonical_validation)==2
assert all(m.self_check(p["input"]) for p in train)

# Two frames fit the exact failing dimensions, even with the generator's
# double-padded separation rule: their padded column intervals are [-1,4]
# and [5,10], which do not overlap.
feasible=[[0]*11 for _ in range(8)]
for (r1,c1,r2,c2),color in [((0,0,3,3),3),((0,6,3,9),4)]:
    for r in range(r1,r2+1):
        for c in range(c1,c2+1):
            if r in (r1,r2) or c in (c1,c2):feasible[r][c]=5
    feasible[r1+1][c1+1]=color
assert len(frames(feasible))==2 and m.self_check(feasible)==[]
inputs=[generated,train[0]["input"],train[1]["input"],feasible]
rivals=[restricted_frame_rival(g) for g in inputs]
assert all(rivals[i+1]!=pair["output"] for i,pair in enumerate(train))
rule_path=next((REPO/"shared/data/base/solutions").rglob("*__"+TASK_ID+".json"))
rule=json.loads(rule_path.read_text())["racket_target"]["target_code"]
report={
 "schema":"audit-frame-contract-v1", "task_id":TASK_ID,"source_state":"unchanged audited source",
 "generator_version":m.VERSION,"generator_path":str(source_path.relative_to(WORK)),
 "generator_sha256":source_hash,"selected_rule_path":str(rule_path.relative_to(WORK)),
 "selected_rule_file_sha256":hashlib.sha256(rule_path.read_bytes()).hexdigest(),
 "selected_rule_source_sha256":hashlib.sha256(rule.encode()).hexdigest(),
 "canonical_ledger_sha256":hashlib.sha256((REPO/"shared/data/canonical/puzzles.jsonl").read_bytes()).hexdigest(),
 "generation_case":{"seed":0,"sample_index":0,"difficulty":"medium","overrides":overrides,
                    "recorded_draws":ctx.recorded_draws(),"overrides_used":ctx.overrides_used(),
                    "observed_frame_count":len(frames(generated)),"frame_bounds":frames(generated),
                    "self_check":m.self_check(generated,difficulty="medium"),"input_index":0},
 "canonical_validation":canonical_validation,
 "input_inventory":[{"index":0,"kind":"generated exact-count failure"},
                    {"index":1,"kind":"public canonical train pair 0"},
                    {"index":2,"kind":"public canonical train pair 1"},
                    {"index":3,"kind":"constructive exact-dimension packing feasibility"}],
 "feasibility_case":{"input_index":3,"shape":[8,11],"frame_bounds":frames(feasible),"self_check":m.self_check(feasible)},
 "rival":"Fill only complete gray frames whose height and width are both at least 4",
 "canonical_expected_outputs":[p["output"] for p in train],
 "scope":{"generated_reproductions":1,"seed_range":[0,0],"sample_index":0,
          "canonical_inputs_checked":3,"canonical_inputs_rejected":2,
          "frequency_estimate":False,"exhaustive_override_audit":False},
 "input_path":"checks/audit/"+TASK_ID+"/input.json", "rival_output_path":"checks/audit/"+TASK_ID+"/rival_output.json"
}
dump("input.json",inputs)
dump("rival_output.json",rivals)
dump("probe.json",report)
print(json.dumps({"task_id":TASK_ID,"source":source_hash,"requested_frames":2,"observed_frames":1,
                  "validator_errors":[],"canonical_rejected":2,"canonical_checked":3,"inputs_for_authority":4},sort_keys=True))
