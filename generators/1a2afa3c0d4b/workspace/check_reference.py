"""Independent NumPy geometry checks against the public Racket authority.

Run from a review packet using review.py run. No selected-rule implementation
is imported or mirrored. NumPy operations compute the diagnostic expectations.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import numpy as np
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "1a2afa3c0d4b"
ORDER = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
SEED = 20261008

def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def grid_sha256(grid):
    return hashlib.sha256(json.dumps(grid,separators=(",",":")).encode()).hexdigest()

def numpy_transform(grid, code):
    array = np.asarray(grid, dtype=np.int64)
    operations = {
        "id": lambda: array.copy(),
        "r1": lambda: np.rot90(array, -1),
        "r2": lambda: np.rot90(array, 2),
        "r3": lambda: np.rot90(array, 1),
        "fh": lambda: np.fliplr(array),
        "fv": lambda: np.flipud(array),
        "tr": lambda: array.T,
        "atr": lambda: np.rot90(array.T, 2),
    }
    return operations[code]().tolist()

def independent_panels(grid):
    body = np.asarray(grid[1:],dtype=np.int64)
    cuts = np.flatnonzero(np.all(body==8,axis=0)).tolist()
    panels=[]
    start=0
    for stop in cuts+[body.shape[1]]:
        panels.append(body[:,start:stop].tolist())
        start=stop+1
    if len(panels)!=3: raise ValueError("Expected three panels")
    return panels

def independent_expected(grid, requested=None):
    a,b,c=independent_panels(grid)
    matches=[code for code in ORDER if numpy_transform(a,code)==b]
    if not matches: raise ValueError("No exact transform maps A to B")
    code=matches[0]
    if requested is not None and matches!=[requested]:
        raise ValueError(f"Expected unique {requested}, got {matches}")
    target=next(v for v in grid[0] if v)
    expected=np.where(np.asarray(numpy_transform(c,code))!=0,target,0).tolist()
    return expected,{"transform_matches":matches,"selected_transform":code,
                     "first_header_color":target,
                     "first_header_column":next(i for i,v in enumerate(grid[0]) if v),
                     "header_colors":[v for v in grid[0] if v]}

def load_generator(root):
    candidates=(root/"generators"/TASK/"generator.py",
                root/"puzzle_generators"/"per_puzzle"/TASK/"generator.py")
    source=next((path for path in candidates if path.is_file()),None)
    if source is None: raise FileNotFoundError("No portable generator source")
    spec=importlib.util.spec_from_file_location("reference_probe_generator",source)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module,source

def prepare_cases(root,gen):
    cases=[]
    for side in (3,4,9):
        difficulty={3:"easy",4:"medium",9:"hard"}[side]
        for mode in ("geometry","color"):
            for code in ORDER:
                index=len(cases)
                overrides={"panel_side":side,"a_mode":mode,"transform":code,
                           "header_color":index%9+1,
                           "header_position":("first","interior","last")[index%3]}
                grid=gen.generate(SEED,index,difficulty=difficulty,**overrides)
                expected,analysis=independent_expected(grid,code)
                cases.append({"kind":"generated","seed":SEED,"sample_index":index,
                              "difficulty":difficulty,"overrides":overrides,"input":grid,
                              "expected":expected,"analysis":analysis,
                              "self_check_errors":gen.self_check(grid,difficulty=difficulty)})
    for pair in canonical_pairs(TASK,root=root,labeled_only=True):
        expected,analysis=independent_expected(pair["input"])
        cases.append({"kind":"canonical","variant":pair["variant"],"split":pair["split"],
                      "pair_index":pair["pair_index"],"input":pair["input"],
                      "expected":expected,"canonical_output":pair["output"],
                      "analysis":analysis,"self_check_errors":gen.self_check(pair["input"])})
    for name in ("empty_query","multiple_header_colors"):
        grid=[row[:] for row in cases[0]["input"]]
        side=len(grid)-1
        if name=="empty_query":
            for row in grid[1:]: row[2*(side+1):]=[0]*side
        else:
            grid[0]=[0]*len(grid[0])
            grid[0][1]=8
            grid[0][2]=1
            grid[0][-1]=9
        expected,analysis=independent_expected(grid)
        cases.append({"kind":"lawful_edge","edge":name,"input":grid,"expected":expected,
                      "analysis":analysis,"self_check_errors":gen.self_check(grid)})
    return cases

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): raise FileExistsError(f"Use a new evidence directory: {args.out}")
    args.out.mkdir(parents=True)
    root=find_root(__file__)
    evidence_dir=args.out.resolve().relative_to(root.parent).as_posix()
    gen,source=load_generator(root)
    generator_hash=sha256_file(source)
    cases=prepare_cases(root,gen)
    assert len(cases)<=64
    inputs=[case["input"] for case in cases]
    (args.out/"inputs.json").write_text(json.dumps(inputs,indent=1)+"\n")
    # Exactly one supported public authority call for the entire bounded population.
    authority=Catalog(root).apply(TASK,inputs,timeout=180)
    (args.out/"authority.json").write_text(json.dumps(authority,indent=1)+"\n")
    failures=[]
    for index,(case,result) in enumerate(zip(cases,authority["results"],strict=True)):
        checks={"validator_accepts":not case["self_check_errors"],
                "racket_output_valid":result["valid_output"] and result["error"] is None,
                "racket_matches_numpy":result["output"]==case["expected"],
                "receipt_input_hash_matches":result["input_sha256"]==grid_sha256(case["input"]),
                "receipt_output_hash_matches":result["output_sha256"]==grid_sha256(result["output"])}
        if case["kind"]=="generated":
            overrides=case["overrides"]
            column=case["analysis"]["first_header_column"]
            actual_position=("first" if column==0 else
                             "last" if column==len(case["input"][0])-1 else "interior")
            checks["requested_header_color_honored"]=(case["analysis"]["first_header_color"]==overrides["header_color"])
            checks["requested_header_position_honored"]=(actual_position==overrides["header_position"])
            checks["requested_panel_side_honored"]=(len(case["input"])-1==overrides["panel_side"])
        if case["kind"]=="canonical":
            checks["numpy_matches_canonical_label"]=case["expected"]==case["canonical_output"]
            checks["racket_matches_canonical_label"]=result["output"]==case["canonical_output"]
        case["checks"]=checks
        case["input_sha256"]=result["input_sha256"]
        case["output_sha256"]=result["output_sha256"]
        if not all(checks.values()): failures.append({"index":index,"kind":case["kind"],"checks":checks})
    source_unchanged=sha256_file(source)==generator_hash==authority["generator_sha256"]
    if not source_unchanged: failures.append({"error":"Generator bytes changed during reference probe"})
    canonical_records=[json.loads(line) for line in canonical_path(root).open()
                       if json.loads(line).get("task_id")==TASK]
    report={"schema":"task-local-numpy-reference-probe-v1","task_id":TASK,
            "status":"pass" if not failures else "fail","generator_sha256":generator_hash,
            "programsource_sha256":sha256_file(__file__),
            "canonical_program_sha256":[hashlib.sha256(row["program_solution"].encode()).hexdigest()
                                         for row in canonical_records],
            "executed_rule_hash":authority["executed_rule_hash"],
            "rule_text_sha256":authority["rule_text_sha256"],
            "source_unchanged":source_unchanged,"numpy_version":np.__version__,
            "python_executable":sys.executable,"runtime_cwd":os.getcwd(),
            "invocation_argv":[sys.executable,*sys.argv],
            "authority_invocation":{"api":"Catalog(root).apply","root":str(root),
                                    "task_id":TASK,"input_count":len(inputs),"timeout":180},
            "verification_command":{"cwd":"packet_root",
                "argv":["python3","review.py","run","python3",
                        "generators/"+TASK+"/workspace/check_reference.py","--out",str(args.out)],
                "evidence_paths":[evidence_dir+"/report.json",evidence_dir+"/inputs.json",
                                  evidence_dir+"/authority.json"]},
            "counts":{"generated":sum(c["kind"]=="generated" for c in cases),
                      "canonical":sum(c["kind"]=="canonical" for c in cases),
                      "lawful_edges":sum(c["kind"]=="lawful_edge" for c in cases),
                      "total":len(cases),"passing":len(cases)-sum("index" in f for f in failures),
                      "failures":len(failures)},
            "coverage":{"panel_sides":[3,4,9],"a_modes":["geometry","color"],
                        "transforms":list(ORDER),"seed":SEED,"sample_indices":[0,47],
                        "header_colors":sorted({c["analysis"]["first_header_color"] for c in cases
                                                if c["kind"]=="generated"}),
                        "header_positions":["first","interior","last"]},
            "failures":failures,"cases":cases}
    (args.out/"report.json").write_text(json.dumps(report,indent=1)+"\n")
    print(json.dumps({k:report[k] for k in ("status","generator_sha256","programsource_sha256","counts")}))
    return 0 if not failures else 1

if __name__=="__main__": raise SystemExit(main())
