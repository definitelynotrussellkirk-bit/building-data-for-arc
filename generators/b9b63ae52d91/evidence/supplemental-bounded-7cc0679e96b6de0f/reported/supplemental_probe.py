"""Supplemental bounded inspection of the known target from the failed draw."""
import json
from pathlib import Path
from reviewer_support import canonical_pairs,find_root,load_selected_generator
root=find_root(__file__)
gen,source,sha=load_selected_generator("b9b63ae52d91",root=root)
def oracle(grid):
    return [[2 if value==8 and grid[len(grid)-1-r][c]==8 else 5 if value==8 else 0 for c,value in enumerate(row)] for r,row in enumerate(grid)]
pairs=canonical_pairs(gen.TASK_ID,root=root,labeled_only=True)
canonical=[oracle(p["input"])==p["output"] and gen.rule_mirror(p["input"])==p["output"] and not gen.self_check(p["input"]) for p in pairs]
assert all(canonical)
checked=0
for band in (None,"easy","medium","hard"):
    for index in range(25):
        grid=gen.generate(17,index,difficulty=band)
        assert not gen.self_check(grid)
        assert gen.rule_mirror(grid)==oracle(grid)
        checked+=1
bad=[{"seed":True,"sample_index":0},{"seed":0,"sample_index":-1},{"seed":0,"sample_index":0,"difficulty":"not-a-band"}]
rejected=0
for args in bad:
    try:gen.generate(**args)
    except (TypeError,ValueError):rejected+=1
assert rejected==len(bad)
report={"task_id":gen.TASK_ID,"generator_sha256":sha,"version":gen.VERSION,"classification":"No issue found within bounded supplemental scope","reason":"Known first target of initial uncommitted audit draw; not an additional contracted audit","canonical_pairs_verified":len(canonical),"python_generated_inputs_checked":checked,"independent_mirror_mismatches":0,"invalid_controls_rejected":rejected,"new_racket_executions":0,"limits":"100 generated inputs at seed17 plus saved canonical labels; no larger battery, admission or exhaustive rule claim."}
Path(__file__).with_name("supplemental-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
