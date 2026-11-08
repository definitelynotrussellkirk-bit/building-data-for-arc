#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3] / "repo"
TARGET = REPO / "generators" / "1120fd69b838" / "generator.py"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]

from reviewer_support import canonical_pairs

spec = importlib.util.spec_from_file_location("audit_1120", TARGET)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

STEPS=((1,0),(-1,0),(0,1),(0,-1))

def components(grid):
    seen=set(); result=[]
    h=len(grid); w=len(grid[0])
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            if value==0 or (r,c) in seen: continue
            seen.add((r,c)); todo=[(r,c)]; cells=[]
            for rr,cc in todo:
                cells.append((rr,cc))
                for dr,dc in STEPS:
                    q=(rr+dr,cc+dc)
                    if 0<=q[0]<h and 0<=q[1]<w and q not in seen and grid[q[0]][q[1]]==value:
                        seen.add(q); todo.append(q)
            result.append(cells)
    result.sort(key=lambda cells:(min(r for r,c in cells),min(c for r,c in cells)))
    return result

def normalize(cells):
    r0=min(r for r,c in cells); c0=min(c for r,c in cells)
    return tuple(sorted((r-r0,c-c0) for r,c in cells))

def rotate(cells):
    cells=normalize(cells); mx=max(r for r,c in cells)
    return normalize([(c,mx-r) for r,c in cells])

def flip(cells):
    cells=normalize(cells); mx=max(c for r,c in cells)
    return normalize([(r,mx-c) for r,c in cells])

def signature(cells):
    cur=normalize(cells); forms=[]
    for _ in range(4):
        forms.append(normalize(cur)); forms.append(normalize(flip(cur))); cur=rotate(cur)
    return min(forms)

def truth(grid):
    comps=components(grid); sig=[signature(c) for c in comps]
    return [[8 if sig[i]==sig[j] else 0 for j in range(len(comps))] for i in range(len(comps))]

def area_rival(grid):
    areas=[len(c) for c in components(grid)]
    return [[8 if areas[i]==areas[j] else 0 for j in range(len(areas))] for i in range(len(areas))]

canonical = canonical_pairs("1120fd69b838", root=REPO)
canonical_fit = sum(area_rival(pair["input"]) == pair["output"] for pair in canonical)
assert canonical_fit == len(canonical)

found=None
for seed in range(10000):
    grids=[mod.generate(seed,i,difficulty="easy") for i in range(5)]
    assert all(mod.self_check(g)==[] for g in grids)
    truths=[truth(g) for g in grids]
    rivals=[area_rival(g) for g in grids]
    if all(truths[i]==rivals[i] for i in range(4)) and truths[4]!=rivals[4]:
        found={
            "schema":"arcpuzzles-audit-semantic-counterexample-v1",
            "task_id":"1120fd69b838",
            "generator_sha256":hashlib.sha256(TARGET.read_bytes()).hexdigest(),
            "declared_version":mod.VERSION,
            "difficulty":"easy",
            "seed":seed,
            "demo_sample_indices":[0,1,2,3],
            "query_sample_index":4,
            "rival":"area_equality",
            "canonical_pairs":len(canonical),
            "canonical_rival_fit_count":canonical_fit,
            "demos":[
                {"sample_index":i,"input":grids[i],"expected_output":truths[i],"rival_output":rivals[i],
                 "areas":[len(c) for c in components(grids[i])],"self_check":mod.self_check(grids[i])}
                for i in range(4)
            ],
            "query":{"sample_index":4,"input":grids[4],"expected_output":truths[4],"rival_output":rivals[4],
                     "areas":[len(c) for c in components(grids[4])],"self_check":mod.self_check(grids[4])},
            "claim":"The area-equality rival fits all four sequential demonstrations but changes the next query.",
        }
        break
if found is None:
    raise SystemExit("no ambiguous sequential lesson found")
out=Path(__file__).with_name("area_lesson.json")
out.write_text(json.dumps(found,indent=2)+"\n")
Path(__file__).with_name("lesson_inputs.json").write_text(json.dumps([x["input"] for x in found["demos"]]+[found["query"]["input"]],indent=2)+"\n")
print(json.dumps({"seed":found["seed"],"demo_areas":[d["areas"] for d in found["demos"]],"query_areas":found["query"]["areas"],"generator_sha256":found["generator_sha256"]},indent=2))
