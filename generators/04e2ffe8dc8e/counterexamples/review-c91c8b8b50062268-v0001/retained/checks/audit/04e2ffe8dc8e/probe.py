"""Bounded source-bound adversarial probe; only writes to this checks directory."""
from __future__ import annotations
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TASK = "04e2ffe8dc8e"
EXPECTED = "21425260e0af633b53e19f217a8e6ba3f5959fa48b77b62a1356156ad465a165"
SOURCE = REPO / "generators" / TASK / "generator.py"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")

def components(grid):
    unseen={(r,c) for r,row in enumerate(grid) for c,value in enumerate(row) if value!=0}
    result=[]
    while unseen:
        first=min(unseen);unseen.remove(first)
        color=grid[first[0]][first[1]];stack=[first];cells=[]
        while stack:
            r,c=stack.pop();cells.append((r,c))
            for pos in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if pos in unseen and grid[pos[0]][pos[1]]==color:
                    unseen.remove(pos);stack.append(pos)
        result.append({"color":color,"size":len(cells),"cells":sorted(cells)})
    return result

def rival(grid):
    objs=components(grid)
    chosen=min(objs,key=lambda obj:(obj["size"],obj["cells"][0]))
    output=deepcopy(grid)
    for r,c in chosen["cells"]:output[r][c]=6
    return output

def load_generator():
    assert digest(SOURCE)==EXPECTED
    assignment=json.loads((WORK/"AUDIT_ASSIGNMENT.json").read_text())
    drawn=next(row for row in assignment["targets"] if row["task_id"]==TASK)
    assert drawn["generator_sha256"]==EXPECTED
    spec=importlib.util.spec_from_file_location("audit04_current",SOURCE)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def generate():
    module=load_generator()
    selected=None;searched=[]
    for seed in range(64):
        grids=[module.generate(seed,index,difficulty="medium") for index in range(5)]
        decoys=[any(value not in (0,3) for row in grid for value in row) for grid in grids]
        searched.append({"seed":seed,"non_green_presence":decoys})
        if decoys==[False,False,False,False,True]:
            selected=(seed,grids);break
    assert selected is not None,"No four-demo witness in bounded seeds 0..63; retain honest failure"
    seed,grids=selected
    cases=[]
    for index,grid in enumerate(grids):
        cases.append({"kind":"four_demo_lesson","role":"demo" if index<4 else "query",
            "seed":seed,"sample_index":index,"difficulty":"medium","overrides":{},
            "self_check":module.self_check(grid,difficulty="medium"),
            "input":grid,"rival_output":rival(grid),"components":components(grid)})
    options={"texture":"decoy","small_size":1}
    grid=module.generate(0,0,difficulty="medium",**options)
    cases.append({"kind":"decoy_override","role":"control","seed":0,"sample_index":0,
        "difficulty":"medium","overrides":options,
        "self_check":module.self_check(grid,difficulty="medium"),
        "input":grid,"rival_output":rival(grid),"components":components(grid)})
    assert all(case["self_check"]==[] for case in cases)
    assert not any(value not in (0,3) for row in grid for value in row)
    tree=ast.parse(SOURCE.read_text())
    payload={"schema":"review-audit-probe-v1","task_id":TASK,"generator_sha256":EXPECTED,
        "generator_path":str(SOURCE.relative_to(WORK)),"declared_examples_needed":module.EXAMPLES_NEEDED,
        "chosen_lesson_seed":seed,"band":"medium","searched":searched,"cases":cases,
        "structural_observations":{"rule_hash_declared":hasattr(module,"RULE_HASH"),
            "self_check_definitions":sum(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="self_check" for n in tree.body)},
        "scope":"Six generated inputs and a bounded seed search; no battery or corpus census. Racket output must be obtained separately with supported arcpuzzles apply."}
    dump("inputs.json",[case["input"] for case in cases]);dump("generation.json",payload)
    print(json.dumps({"task_id":TASK,"generator_sha256":EXPECTED,"chosen_seed":seed,"seeds_tried":len(searched),"grids":len(cases),"all_self_checks_pass":True},sort_keys=True))

def compare():
    assert digest(SOURCE)==EXPECTED
    generation=json.loads((HERE/"generation.json").read_text())
    authority=json.loads((HERE/"racket.json").read_text())
    assert authority["generator_sha256"]==EXPECTED
    assert authority["executed_rule_hash"]=="c67640298f12"
    assert authority["rule_hash_matches_catalog"] is True
    assert len(authority["results"])==len(generation["cases"])
    reports=[]
    for case,row in zip(generation["cases"],authority["results"]):
        assert row["error"] is None and row["valid_output"] is True,row
        assert row["input"]==case["input"]
        output=row["output"];prediction=case["rival_output"]
        disagreement=[{"row":r,"column":c,"authority":value,"rival":prediction[r][c]}
            for r,line in enumerate(output) for c,value in enumerate(line) if prediction[r][c]!=value]
        reports.append({**case,"racket_output":output,"racket_input_sha256":row["input_sha256"],
            "racket_output_sha256":row["output_sha256"],"generator_domain":row.get("generator_domain"),
            "rival_equals_racket":not disagreement,"disagreements":disagreement})
    assert all(row["rival_equals_racket"] for row in reports[:4])
    assert not reports[4]["rival_equals_racket"]
    assert reports[5]["rival_equals_racket"]
    summary={"schema":"review-audit-finding-v1","task_id":TASK,"classification":"reproduced teaching shortcut and override mismatch",
        "generator_sha256":EXPECTED,"rule_hash":authority["executed_rule_hash"],
        "generator_unchanged":True,"four_demo_lesson":{"seed":generation["chosen_lesson_seed"],"difficulty":"medium","demo_sample_indices":[0,1,2,3],"query_sample_index":4,
            "rival_fits_all_four_demos":True,"query_disagreement_count":len(reports[4]["disagreements"]),"all_inputs_pass_self_check":True},
        "decoy_override":{"seed":0,"sample_index":0,"difficulty":"medium","overrides":{"texture":"decoy","small_size":1},"non_green_foreground_cells":0,"rival_equals_racket":True,"self_check":[]},
        "cases":reports,"source_hashes":{"generator":digest(SOURCE),"canonical":digest(REPO/"shared/data/canonical/puzzles.jsonl"),"review_index":digest(REPO/"generators"/TASK/"evidence/review_index.json"),"probe":digest(Path(__file__))},
        "evidence_hashes":{name:digest(HERE/name) for name in ["inputs.json","generation.json","racket.json"]},
        "limitations":["Fresh bounded reproduction of an existing unresolved finding, extended to a four-demo lesson.","No generator/rule/policy changed; no linter or full battery rerun.","One finite rival and one lesson do not characterize all generated lessons.","Correct labels are preserved; the defect is insufficient demonstrations to distinguish the color-qualified selection rule."]}
    dump("finding.json",summary)
    print(json.dumps({"task_id":TASK,"generator_sha256":EXPECTED,"rule_hash":authority["executed_rule_hash"],"four_demo_lesson":summary["four_demo_lesson"],"decoy_override":summary["decoy_override"]},sort_keys=True))

if __name__=="__main__":
    if sys.argv[1:]==["generate"]:generate()
    elif sys.argv[1:]==["compare"]:compare()
    else:raise SystemExit("Usage: probe.py generate|compare")
