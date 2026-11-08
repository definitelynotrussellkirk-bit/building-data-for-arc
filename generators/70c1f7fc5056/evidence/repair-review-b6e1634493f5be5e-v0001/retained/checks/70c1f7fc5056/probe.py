"""One bounded anchor-alignment teaching probe; no source or audit changes."""
import hashlib
import json
from pathlib import Path
from arcpuzzles import Catalog
from reviewer_support import load_selected_generator, find_root

TASK = "70c1f7fc5056"
gen, source, digest = load_selected_generator(TASK)
root = find_root(source)
grids = [gen.generate(0, i) for i in range(4)]

def first_pixel_rival(grid):
    cells = [(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,9)]
    top, left = min(r for r,c,v in cells), min(c for r,c,v in cells)
    offsets = [(r-top,c-left,v) for r,c,v in cells]
    first_r, first_c, _ = offsets[0]
    out = [[0]*len(grid[0]) for _ in grid]
    for r,c,v in cells:
        out[r][c] = v
    for ar,row in enumerate(grid):
        for ac,value in enumerate(row):
            if value == 9:
                for dr,dc,v in offsets:
                    rr,cc = ar+dr-first_r,ac+dc-first_c
                    if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                        out[rr][cc] = v
    return out

result = Catalog(root).apply(TASK, grids)
pairs = []
for index,(grid,row) in enumerate(zip(grids,result["results"])):
    if row.get("error") or row.get("output") is None:
        raise RuntimeError(str(row))
    rival = first_pixel_rival(grid)
    pairs.append({"sample_index":index,"input":grid,"canonical_output":row["output"],
                  "rival_output":rival,"rival_matches":rival==row["output"],
                  "domain_errors":gen.self_check(grid)})
assert len(pairs)==4 and all(not p["domain_errors"] for p in pairs)
assert [p["rival_matches"] for p in pairs] == [True,True,True,False]
report = {
    "task_id":TASK,"status":"concrete_teaching_blind_spot","consumer":"lesson construction and finite teaching contract",
    "source_path":str(source.relative_to(root)),"source_sha256":digest,
    "probe_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "command":"PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python ../checks/70c1f7fc5056/probe.py",
    "seed":0,"demonstration_indices":[0,1,2],"query_index":3,
    "rival":"Keep the source prototype, but align its first row-major occupied cell to each color-9 anchor instead of aligning its bounding-box top-left.",
    "observation":"The rival matches all three executed demonstration labels and differs on the fourth lawful generated input. Its prototype has an empty bounding-box top-left, exposing the anchor convention.",
    "racket_run":True,"racket_scope":"Four canonical applications through public Catalog.apply; rival predictions are independent Python, not Racket.",
    "executed_rule_hash":result.get("executed_rule_hash"),"rule_text_sha256":result.get("rule_text_sha256"),
    "recommendation":"When a query prototype has an empty bounding-box top-left, include an executed demonstration with that property so the anchor convention is identifiable against first-occupied-cell alignment.",
    "existing_audits":"Two current unresolved audits remain unchanged; known documentation and ignored-control findings were not rerun.",
    "limits":["One bounded seed and one rival; no full battery or universal ambiguity claim.","These are four lawful consecutive generator draws; no claim that a production lesson assembler uses this exact episode.","No generator, canonical authority, approval, or audit disposition was edited."],
    "pairs":pairs
}
out=Path(__file__).with_name("peer-review.json")
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:report[k] for k in ("status","source_sha256","executed_rule_hash","racket_run")}))
print(str(out))
