#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK = "0e09cb9954e1"
source = (Path.cwd() / "generators" / TASK / "generator.py").resolve()
spec = importlib.util.spec_from_file_location(f"audit_{TASK}", source)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()

def qualifying_pairs(grid):
    rows=[]
    h,w=len(grid),len(grid[0])
    for r in range(h-1):
        for c in range(w-1):
            tl,tr=grid[r][c],grid[r][c+1]
            bl,br=grid[r+1][c],grid[r+1][c+1]
            if tl != 0 and tl == br and tr == 0 and bl == 0:
                rows.append({"r":r,"c":c,"orientation":"main","color":tl})
            if tr != 0 and tr == bl and tl == 0 and br == 0:
                rows.append({"r":r,"c":c,"orientation":"anti","color":tr})
    return rows

base = {"seed": 90210, "sample_index": 5, "difficulty": "medium"}
comparisons=[]
for axis,left,right in [
    ("palette_kind","warm","cool"),
    ("palette_size",1,9),
    ("n_distinct_colors",1,9),
    ("texture","default","cool"),
]:
    gl=mod.generate(**base, **{axis:left})
    gr=mod.generate(**base, **{axis:right})
    comparisons.append({
        "axis":axis,"left":left,"right":right,
        "identical":gl==gr,
        "left_sha256":digest(gl),"right_sha256":digest(gr),
        "shape":[len(gl),len(gl[0])],
        "self_check_left":mod.self_check(gl),"self_check_right":mod.self_check(gr),
    })

unknown = mod.generate(**base, typoed_axis=123)

repeat_witness=None
for difficulty in ("easy","medium","hard"):
    for seed in range(1000):
        grid=mod.generate(seed, 0, difficulty=difficulty)
        pairs=qualifying_pairs(grid)
        colors=[p["color"] for p in pairs]
        if len(colors) != len(set(colors)):
            repeat_witness={
                "seed":seed,"sample_index":0,"difficulty":difficulty,
                "shape":[len(grid),len(grid[0])],
                "pairs":pairs,"grid":grid,"grid_sha256":digest(grid),
                "self_check":mod.self_check(grid),
            }
            break
    if repeat_witness:
        break

junk = [[0]*5 for _ in range(5)]
junk[0][0]=1; junk[1][1]=1
junk[4][4]=99

report={
    "schema":"audit-0e09cb9954e1-v1",
    "task_id":TASK,
    "generator_source":str(source),
    "generator_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
    "version":getattr(mod,"VERSION",None),
    "rule_hash":getattr(mod,"RULE_HASH",None),
    "same_seed_override_comparisons":comparisons,
    "unknown_override":{
        "call":{**base,"typoed_axis":123},
        "accepted":True,"grid_sha256":digest(unknown),
        "shape":[len(unknown),len(unknown[0])],
        "self_check":mod.self_check(unknown),
    },
    "repeated_color_witness":repeat_witness,
    "acceptance_only_self_check_witness":{
        "grid":junk,"self_check":mod.self_check(junk),
        "note":"contains one qualifying pair plus an out-of-range color 99",
    },
}
Path(__file__).with_name("probe.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({
    "dead_axis_identical":{r["axis"]:r["identical"] for r in comparisons},
    "unknown_override_accepted":True,
    "repeated_color_witness":None if repeat_witness is None else {k:repeat_witness[k] for k in ("seed","difficulty","shape")},
    "junk_self_check":report["acceptance_only_self_check_witness"]["self_check"],
},indent=2))
