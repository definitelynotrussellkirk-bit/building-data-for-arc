"""Read-only audit: canonical-fitting collinear overlap tie policy."""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]/"repo"
sys.path.insert(0,str(ROOT/"shared/runtime"))
sys.path.insert(0,str(ROOT/"src"))
from reviewer_support import canonical_pairs,load_selected_generator
from arcpuzzles import Catalog

TASK="615b0cf22405"
gen,source,source_hash=load_selected_generator(TASK,root=ROOT)


def fill(grid, *, maximum_tie=False):
    """Pixel oracle: vertical interiors first, then original cells, then horizontal interiors."""
    cells=defaultdict(list)
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            if value:
                cells[value].append((r,c))
    horizontal=[]
    vertical=[]
    for color,points in sorted(cells.items()):
        assert len(points)==2,(color,points)
        (r0,c0),(r1,c1)=points
        if r0==r1:
            horizontal.append((color,r0,min(c0,c1),max(c0,c1)))
        if c0==c1:
            vertical.append((color,c0,min(r0,r1),max(r0,r1)))
    choose=max if maximum_tie else min
    out=[row[:] for row in grid]
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            vm=[color for color,col,lo,hi in vertical if col==c and lo<r<hi]
            if vm:
                out[r][c]=choose(vm)
            elif value==0:
                hm=[color for color,rr,lo,hi in horizontal if rr==r and lo<c<hi]
                out[r][c]=choose(hm) if hm else 0
    return out


def differences(a,b):
    return [[r,c,a[r][c],b[r][c]] for r in range(len(a)) for c in range(len(a[0])) if a[r][c]!=b[r][c]]


canonical=canonical_pairs(TASK,root=ROOT,labeled_only=True)
assert len(canonical)==3
assert all(fill(pair["input"])==pair["output"] for pair in canonical)
assert all(fill(pair["input"],maximum_tie=True)==pair["output"] for pair in canonical)
witness=None
searched=0
for seed in (0,1,17):
    window=[]
    for index in range(100):
        grid=gen.generate(seed,index)
        assert gen.self_check(grid)==[]
        intended=fill(grid)
        rival=fill(grid,maximum_tie=True)
        window.append({"sample_index":index,"input":grid,"python_expected":intended,
                       "rival_output":rival,"self_check":[],"rival_matches":intended==rival})
        searched+=1
        if len(window)>4:
            window.pop(0)
        if len(window)==4 and all(p["rival_matches"] for p in window[:3]) and not window[3]["rival_matches"]:
            witness={"seed":seed,"difficulty":None,"start_sample_index":index-3,
                     "sample_indices":[p["sample_index"] for p in window],"pairs":window[:]}
            break
    if witness:
        break
assert witness,"No witnessed ambiguity in the bounded search"
report={"schema":"615b0cf22405-collinear-tie-audit-v1","task_id":TASK,
        "generator_version":gen.VERSION,"generator_sha256":source_hash,
        "source":str(source.relative_to(ROOT)),
        "finding":"The maximum-color collinear tie rival fits all canonical labels and all three generated demonstrations, then changes the query.",
        "rival":"Preserve vertical-over-horizontal and original-cell precedence, but choose maximum rather than minimum when multiple same-orientation endpoint spans cover one cell.",
        "canonical_pairs":len(canonical),"canonical_rival_matches":len(canonical),
        "searched_pairs":searched,"witness":witness,
        "query_diff_cells":differences(witness["pairs"][3]["python_expected"],witness["pairs"][3]["rival_output"]),
        "rule_hash_declared":getattr(gen,"RULE_HASH",None),
        "semantic_contract_present":any(hasattr(gen,k) for k in ("SEMANTIC_RIVALS","LESSON_COMPETITORS","lesson_identifiable")),
        "status":"python_witness_pending_racket"}
(HERE/"candidate.json").write_text(json.dumps(report,indent=2)+"\n")
summary={key:report[key] for key in ("status","generator_sha256","searched_pairs","canonical_rival_matches","query_diff_cells")}
summary.update(seed=witness["seed"],sample_indices=witness["sample_indices"])
print(json.dumps(summary),flush=True)
if "--python-only" in sys.argv:
    raise SystemExit(0)

inputs=[p["input"] for p in canonical]+[p["input"] for p in witness["pairs"]]
receipt=Catalog(ROOT).apply(TASK,inputs,allow_unapproved=True,timeout=150)
assert receipt["rule_hash_matches_catalog"]
expected=[p["output"] for p in canonical]+[p["python_expected"] for p in witness["pairs"]]
assert len(receipt["results"])==len(expected)
checks=[]
for index,(wanted,result) in enumerate(zip(expected,receipt["results"])):
    assert result["error"] is None,result
    assert result["output"]==wanted,index
    checks.append({"index":index,"input_sha256":result["input_sha256"],
                   "output_sha256":result["output_sha256"],"racket_matches_python_expected":True})
for pair,result in zip(witness["pairs"],receipt["results"][len(canonical):]):
    pair["authority_output"]=result["output"]
report.update(status="racket_confirmed_canonical_fitting_lesson_ambiguity",
              executed_rule_hash=receipt["executed_rule_hash"],
              rule_hash_matches_catalog=receipt["rule_hash_matches_catalog"],racket_checks=checks)
target=HERE/"evidence.json"
target.write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":report["status"],"report":str(target),
                  "executed_rule_hash":report["executed_rule_hash"],"racket_pairs":len(checks),
                  "seed":witness["seed"],"sample_indices":witness["sample_indices"],
                  "query_diff_cells":report["query_diff_cells"]},indent=2))
