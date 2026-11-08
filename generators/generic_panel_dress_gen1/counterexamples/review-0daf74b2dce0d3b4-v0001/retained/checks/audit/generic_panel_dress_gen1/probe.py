#!/usr/bin/env python3
"""Read-only finite positional-rival audit; all final labels use actual Racket."""
from __future__ import annotations
import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys
import traceback
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import find_root, load_selected_generator

TASK = "generic_panel_dress_gen1"
EXPECTED_SOURCE = "4d334d35eb30d0b798220259917fa2e082b8b6834152cd826b376640e4fbf64d"
HERE = Path(__file__).resolve().parent

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def dump(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")

def positional_screen(module,g):
    """Screen only: pair panels and loose shapes in component reading order."""
    bg=Counter(v for row in g for v in row if v!=0).most_common(1)[0][0]
    objects=module._comps(g,bg); cellsets=[set(obj) for obj in objects]
    def touches(i,j):
        return any((r+dr,c+dc) in cellsets[j] for r,c in objects[i]
                   for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)))
    pi=[i for i in range(len(objects)) if any(i!=j and touches(i,j) for j in range(len(objects)))]
    panels=[objects[i] for i in pi]; shapes=[objects[i] for i in range(len(objects)) if i not in pi]
    if len(panels)!=len(shapes):
        raise ValueError("Unexpected screen object inventory")
    br=min(r for obj in panels for r,c in obj); bc=min(c for obj in panels for r,c in obj)
    er=max(r for obj in panels for r,c in obj); ec=max(c for obj in panels for r,c in obj)
    out=[[0]*(ec-bc+1) for _ in range(er-br+1)]
    for panel,shape in zip(panels,shapes):
        pr=min(r for r,c in panel); pc=min(c for r,c in panel)
        pe=max(r for r,c in panel); ce=max(c for r,c in panel)
        sr=min(r for r,c in shape); sc=min(c for r,c in shape)
        se=max(r for r,c in shape); cs=max(c for r,c in shape)
        mr=((pe-pr)-(se-sr))//2; mc=((ce-pc)-(cs-sc))//2
        for r in range(pr,pe+1):
            for c in range(pc,ce+1): out[r-br][c-bc]=g[panel[0][0]][panel[0][1]]
        for r,c in shape: out[pr+mr-br+r-sr][pc+mc-bc+c-sc]=g[r][c]
    return out

def application(program,grid):
    if not program.startswith("(rule!") or not program.endswith(")"):
        raise ValueError("Unexpected emitted source form")
    literal="'("+" ".join("("+" ".join(map(str,row))+")" for row in grid)+")"
    return "("+program[len("(rule!"):-1]+" "+literal+")"

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-seeds",type=int,default=64)
    args=parser.parse_args()
    root=find_root(__file__)
    module,source,source_hash=load_selected_generator(TASK,root=root)
    if source_hash!=EXPECTED_SOURCE: raise ValueError("Assigned source bytes changed")
    program=module.PROGRAM
    needle="(shp (find-first (lambda (s) (= (holes s) ndots)) shapes))"
    if program.count(needle)!=1: raise ValueError("Rival replacement not source-bound")
    rival=program.replace(needle,"(shp (list-ref shapes (index-of panels pan)))",1)
    (HERE/"emitted_program.rkt").write_text(program)
    (HERE/"positional_rival.rkt").write_text(rival)
    report={"schema":"panel-dress-read-only-audit-v1","task_id":TASK,"source_sha256":source_hash,
            "program_sha256":hashlib.sha256(program.encode()).hexdigest(),
            "rival_program_sha256":hashlib.sha256(rival.encode()).hexdigest(),
            "source_path":str(source.relative_to(root)),"status":"screening","screen":[],"executions":[],
            "runtime":racket_runtime_status(),"argv":[sys.executable,*sys.argv],"actual_cwd":str(Path.cwd()),
            "rival_description":"Pair each touching panel with the isolated shape having the same component reading-order rank; ignore hole count.",
            "limitations":["Finite screen of ordinary easy episodes, not exhaustive generation or semantic certification.",
                           "Python screen predicts candidates only; conclusions use the exact actual Racket results retained below.",
                           "No selected generator, emitted authority, shared source, or approval record is modified."]}
    candidate=None
    for seed in range(args.max_seeds):
        before=random.getstate()
        task=module.generate_task(seed,difficulty="easy")
        fit=all(positional_screen(module,pair["input"])==pair["output"] for pair in task["train"])
        query_diff=[i for i,pair in enumerate(task["test"]) if positional_screen(module,pair["input"])!=pair["output"]]
        report["screen"].append({"seed":seed,"n_train":len(task["train"]),"n_test":len(task["test"]),
                                "python_screen_fits_demonstrations":fit,"python_screen_differing_queries":query_diff,
                                "global_rng_unchanged":before==random.getstate()})
        if fit and query_diff:
            candidate=(seed,task); break
    if candidate is None:
        candidate=(0,module.generate_task(0,difficulty="easy"))
        report["screen_candidate_found"]=False
    else:
        report["screen_candidate_found"]=True
    seed,task=candidate
    report.update(seed=seed,difficulty="easy",task=task,deterministic=task==module.generate_task(seed,difficulty="easy"),status="executing")
    dump("probe.json",report)
    bridge=RacketBridge(timeout=20.0,max_calls_before_restart=128)
    try:
        for split in ("train","test"):
            for index,pair in enumerate(task[split]):
                entry={"split":split,"pair_index":index,"input":copy.deepcopy(pair["input"]),
                       "input_sha256":digest(pair["input"]),"stored_python_output":pair["output"]}
                for label,body in (("emitted",program),("positional_rival",rival)):
                    expr=application(body,pair["input"])
                    try:
                        actual=bridge.eval_text(expr)
                        entry[label]={"actual_racket_output":actual,"output_sha256":digest(actual),
                                      "expression":expr,"expression_sha256":hashlib.sha256(expr.encode()).hexdigest()}
                    except Exception as exc:
                        entry[label]={"error":f"{type(exc).__name__}: {exc}","expression":expr,"traceback":traceback.format_exc()}
                report["executions"].append(entry)
                dump("probe.json",report)
        errors=[entry for entry in report["executions"] if any("error" in entry[key] for key in ("emitted","positional_rival"))]
        if errors:
            report["status"]="execution_failure"
        else:
            report["stored_labels_match_actual_racket"]=all(entry["stored_python_output"]==entry["emitted"]["actual_racket_output"] for entry in report["executions"])
            train=[entry for entry in report["executions"] if entry["split"]=="train"]
            test=[entry for entry in report["executions"] if entry["split"]=="test"]
            report["racket_rival_fits_all_demonstrations"]=all(entry["emitted"]["actual_racket_output"]==entry["positional_rival"]["actual_racket_output"] for entry in train)
            report["racket_rival_differing_query_indices"]=[entry["pair_index"] for entry in test if entry["emitted"]["actual_racket_output"]!=entry["positional_rival"]["actual_racket_output"]]
            report["status"]="lesson_ambiguity" if report["racket_rival_fits_all_demonstrations"] and report["racket_rival_differing_query_indices"] else "no_ambiguity_on_checked_episode"
            if not report["stored_labels_match_actual_racket"]: report["status"]="stored_output_mismatch"
        report["source_unchanged_at_end"]=hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
        dump("probe.json",report)
        print(json.dumps({key:report[key] for key in ("status","seed","difficulty","deterministic","screen_candidate_found","stored_labels_match_actual_racket","racket_rival_fits_all_demonstrations","racket_rival_differing_query_indices","source_unchanged_at_end") if key in report},sort_keys=True))
        return 0
    finally:
        bridge.shutdown()

if __name__=="__main__": raise SystemExit(main())
