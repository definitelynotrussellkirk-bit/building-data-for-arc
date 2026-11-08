#!/usr/bin/env python3
"""Source-bound adversarial probe for 287967e33b21."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "repo"
TASK = "287967e33b21"
sys.path.insert(0, str(ROOT / "shared/runtime"))
path = ROOT / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location("audit_target", path)
gen = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(gen)

interior_only=[[0]*9 for _ in range(9)]
interior_only[4][4]=7; interior_only[4][5]=7
border_only=[[0]*9 for _ in range(9)]
border_only[0][3]=7; border_only[1][3]=7

same_palette_outputs = gen.generate(123,4,palette_kind="warm") == gen.generate(123,4,palette_kind="cool")
ignored=[]
for axis,value in {
    "anchor_corner":True,
    "asymmetry_force":True,
    "palette_size":1,
    "position_bias":"fixed",
    "n_distinct_colors":1,
    "other":3,
}.items():
    try:
        base=gen.generate(123,4)
        changed=gen.generate(123,4,**{axis:value})
        ignored.append({"axis":axis,"accepted":True,"same_output":changed==base})
    except Exception as exc:
        ignored.append({"axis":axis,"accepted":False,"error":f"{type(exc).__name__}: {exc}"})

try:
    gen.generate(0,0,difficulty="easy",grid_h=16)
    easy_grid_h_16={"accepted":True}
except Exception as exc:
    easy_grid_h_16={"accepted":False,"error":f"{type(exc).__name__}: {exc}"}

report={
    "schema":"arc-audit-validator-controls-v1",
    "task_id":TASK,
    "generator_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
    "interior_only_input":interior_only,
    "interior_only_self_check":gen.self_check(interior_only),
    "interior_only_violates_declared_invariant":"no border-touching color-7 component",
    "border_only_input":border_only,
    "border_only_self_check":gen.self_check(border_only),
    "border_only_violates_declared_invariant":"no fully interior color-7 component",
    "palette_warm_equals_cool":same_palette_outputs,
    "other_advertised_axes":ignored,
    "advertised_grid_h_16_under_easy":easy_grid_h_16,
}
out=Path(__file__).with_name("validator_override_result.json")
out.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({
    "generator_sha256":report["generator_sha256"],
    "interior_only_self_check":report["interior_only_self_check"],
    "border_only_self_check":report["border_only_self_check"],
    "palette_warm_equals_cool":same_palette_outputs,
    "other_advertised_axes":ignored,
    "advertised_grid_h_16_under_easy":easy_grid_h_16,
},indent=2))
if report["interior_only_self_check"] or report["border_only_self_check"] or not same_palette_outputs:
    raise SystemExit(1)
