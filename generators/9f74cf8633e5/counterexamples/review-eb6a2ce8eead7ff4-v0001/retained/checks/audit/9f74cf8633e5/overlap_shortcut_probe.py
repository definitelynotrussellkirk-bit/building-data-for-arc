#!/usr/bin/env python3
"""Source-bound adversarial probe for 9f74cf8633e5."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK = "9f74cf8633e5"
sys.path.insert(0, str(ROOT / "shared/runtime"))
path = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_target", path)
gen = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(gen)


def active_centers(grid):
    out=[]
    for r in range(1,len(grid)-1):
        for c in range(1,len(grid[0])-1):
            vals=[grid[r-1][c-1],grid[r-1][c+1],grid[r+1][c-1],grid[r+1][c+1]]
            if grid[r][c] == 0 and vals[0] != 0 and all(v == vals[0] for v in vals):
                out.append((r,c,vals[0]))
    return out


def footprint(center):
    r,c,_=center
    return {(rr,cc) for rr in range(r-1,r+2) for cc in range(c-1,c+2)}


def isolated_only_rival(grid):
    out=[list(row) for row in grid]
    centers=active_centers(grid)
    fps=[footprint(x) for x in centers]
    for i,(r,c,color) in enumerate(centers):
        if all(not (fps[i] & fps[j]) for j in range(len(fps)) if i != j):
            out[r][c]=color
    return out

row=None
with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as f:
    for line in f:
        item=json.loads(line)
        if item.get("task_id") == TASK:
            row=item; break
assert row
pairs=list(row.get("train",[]))
test=row.get("test",[])
pairs += test if isinstance(test,list) else ([test] if test else [])
canonical_fit=sum(isolated_only_rival(p["input"]) == p["output"] for p in pairs)

generated=0
mismatches=[]
for band in ("easy","medium","hard"):
    for index in range(100):
        grid=gen.generate(8801,index,difficulty=band)
        authoritative=gen.rule_mirror(grid)
        generated += 1
        if isolated_only_rival(grid) != authoritative:
            mismatches.append({"band":band,"index":index,"grid":grid})

# Two same-color valid centers at (2,2) and (2,4) share diagonal cells and
# overlapping 3x3 footprints. The local rule fills both; the rival fills none.
counterexample=[[0]*7 for _ in range(7)]
for r,c in ((1,1),(1,3),(1,5),(3,1),(3,3),(3,5)):
    counterexample[r][c]=4
rule_output=gen.rule_mirror(counterexample)
rival_output=isolated_only_rival(counterexample)
report={
    "schema":"arc-audit-overlap-shortcut-v1",
    "task_id":TASK,
    "generator_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
    "rule_hash":gen.RULE_HASH,
    "rival":"fill a valid center only when its 3x3 footprint is disjoint from every other valid center",
    "canonical_pairs_checked":len(pairs),
    "canonical_pairs_fit":canonical_fit,
    "generated_samples_checked":generated,
    "generated_mismatches":len(mismatches),
    "counterexample_input":counterexample,
    "counterexample_active_centers":active_centers(counterexample),
    "counterexample_self_check":gen.self_check(counterexample),
    "rule_output":rule_output,
    "rival_output":rival_output,
    "outputs_differ":rule_output != rival_output,
    "scope":"Finite check of canonical labeled pairs and 100 default samples per band; not a universal proof.",
}
out=Path(__file__).with_name("overlap_shortcut_result.json")
out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:report[k] for k in ("generator_sha256","canonical_pairs_checked","canonical_pairs_fit","generated_samples_checked","generated_mismatches","counterexample_self_check","outputs_differ")},indent=2))
if canonical_fit != len(pairs) or mismatches or not report["outputs_differ"]:
    raise SystemExit(1)
