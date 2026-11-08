"""Findings-only probe: advertised discard vs canonical retained prototype."""
import hashlib,json
from pathlib import Path
from reviewer_support import canonical_path,find_root,load_selected_generator
ROOT=find_root(__file__)
gen,source,sha=load_selected_generator("70c1f7fc5056",root=ROOT)
OUT=Path(__file__).resolve().parent

def expected(grid,keep):
    cells=[(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,9)]
    top=min(r for r,c,v in cells);left=min(c for r,c,v in cells)
    offsets=[(r-top,c-left,v) for r,c,v in cells]
    anchors=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==9]
    result=[[0]*len(grid[0]) for _ in grid]
    for ar,ac in ([(top,left)] if keep else [])+anchors:
        for dr,dc,v in offsets:
            if 0<=ar+dr<len(grid) and 0<=ac+dc<len(grid[0]):result[ar+dr][ac+dc]=v
    return result

rows=[json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if json.loads(line).get("task_id")==gen.TASK_ID]
pairs=[pair for row in rows for split in ("train","test") for pair in row.get(split,[]) if "output" in pair]
keep=[expected(p["input"],True)==p["output"] for p in pairs]
discard=[expected(p["input"],False)==p["output"] for p in pairs]
assert all(keep)
assert not any(discard)
samples=[]
for band in (None,"easy","hard"):
    for index in range(40):
        grid=gen.generate(17,index,difficulty=band)
        samples.append({"band":band,"index":index,"self_check":gen.self_check(grid),"discard_changes_output":expected(grid,False)!=expected(grid,True)})
assert all(not r["self_check"] for r in samples)
control=gen.generate(17,0)
ignored=[]
for override in ({"palette_kind":"warm"},{"palette_kind":"cool"},{"palette_kind":"not-a-palette"},{"texture":"not-a-texture"},{"unrecognized_axis":1}):
    generated=gen.generate(17,0,**override)
    ignored.append({"override":override,"accepted":True,"same_as_default":generated==control})
assert all(r["same_as_default"] for r in ignored)
witness={"input":control,"keep_prototype_output":expected(control,True),"documented_discard_output":expected(control,False)}
(OUT/"witness.json").write_text(json.dumps(witness,indent=2)+"\n")
(OUT/"input.json").write_text(json.dumps(control)+"\n")
report={"task_id":gen.TASK_ID,"version":gen.VERSION,"generator_sha256":sha,"source":str(source.relative_to(ROOT)),"canonical_pairs_checked":len(pairs),"retain_prototype_matches":sum(keep),"documented_discard_matches":sum(discard),"valid_generated_samples":len(samples),"self_check_errors":sum(bool(r["self_check"]) for r in samples),"discard_changes_generated_output":sum(r["discard_changes_output"] for r in samples),"ignored_override_probes":ignored,"semantic_contract_declared":all(hasattr(gen,name) for name in ("strict_canonical_like","SEMANTIC_WITNESSES","lesson_identifiable")),"scope":"Official canonical labels plus 120 Python-generated inputs; this command does not execute Racket.","findings":["Documentation contradicts all five canonical pairs: the original prototype is retained, not discarded.","Declared palette_kind and helpful texture controls are ignored; invalid/unknown requests are silently accepted.","No semantic contract is declared; lesson identifiability was not established."]}
(OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
