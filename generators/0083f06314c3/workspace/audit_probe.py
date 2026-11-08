#!/usr/bin/env python3
"""Findings-only audit replay for the two assigned, unmodified generators.

Run from packet root through run_with_racket.py, passing this task-relative
script path. Reports include exact counterexamples and real Racket feedback.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TARGETS = ("cf6ef609da0d", "239a0d1db1cd")


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def components(grid, start_row=0):
    remaining = {(r, c) for r in range(start_row, len(grid)) for c in range(len(grid[0])) if grid[r][c]}
    result = []
    while remaining:
        first = min(remaining)
        color = grid[first[0]][first[1]]
        pending, found = [first], {first}
        remaining.remove(first)
        while pending:
            r, c = pending.pop()
            for q in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if q in remaining and grid[q[0]][q[1]] == color:
                    remaining.remove(q)
                    found.add(q)
                    pending.append(q)
        result.append((color, found))
    return result


def gallery(grid, largest):
    objects = components(grid, 1)
    shapes = []
    for color in [v for v in grid[0] if v]:
        candidates = [cells for value, cells in objects if value == color]
        if not candidates:
            raise ValueError("key color has no body object")
        cells = max(candidates, key=len) if largest else candidates[0]
        r0, c0 = min(r for r,c in cells), min(c for r,c in cells)
        h, w = max(r for r,c in cells)-r0+1, max(c for r,c in cells)-c0+1
        shape = [[0]*w for _ in range(h)]
        for r,c in cells:
            shape[r-r0][c-c0] = color
        shapes.append(shape)
    if not shapes:
        raise ValueError("empty key")
    out = [[0]*(sum(len(s[0]) for s in shapes)+len(shapes)-1) for _ in range(max(map(len,shapes)))]
    left = 0
    for shape in shapes:
        for r,row in enumerate(shape):
            out[r][left:left+len(row)] = row
        left += len(shape[0])+1
    return out


def execute(args):
    from arc_repl.racket_bridge import RacketBridge
    from scripts.rule_smoke import load_rules, rule_application
    rules = load_rules(TARGETS)
    records = {d["task_id"]: d for s in Path("data/canonical/puzzles.jsonl").open()
               if (d := json.loads(s)).get("task_id") in TARGETS}
    out = Path(args.out)
    bridge = RacketBridge(max_calls_before_restart=120)
    try:
        for tid in TARGETS:
            gen = importlib.import_module(f"puzzle_generators.per_puzzle.{tid}.generator")
            report = {"task_id": tid, "generator_sha256": hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
                      "generator_unchanged": True, "default_draws": 0, "default_racket_checked": 0,
                      "default_failures": [], "component_sizes": Counter(), "same_color_body_competition": 0}
            for band in ("easy", "medium", "hard"):
                for i in range(args.count):
                    try:
                        grid = gen.generate(5000+i, i, difficulty=band)
                        report["default_draws"] += 1
                        objs = components(grid, 1 if tid == TARGETS[1] else 0)
                        report["component_sizes"].update(str(len(cells)) for color,cells in objs)
                        if tid == TARGETS[1]:
                            c = Counter(color for color,cells in objs)
                            report["same_color_body_competition"] += any(n>1 for n in c.values())
                        if i < 20:
                            expected = bridge.eval_text(rule_application(rules[tid], grid))
                            report["default_racket_checked"] += 1
                            if tid == TARGETS[1]:
                                if expected != gallery(grid, True) or expected != gallery(grid, False):
                                    report["default_failures"].append({"seed":5000+i,"i":i,"band":band,"reason":"gallery parity"})
                    except Exception as exc:
                        report["default_failures"].append({"seed":5000+i,"i":i,"band":band,"error":str(exc)})
            base = gen.generate(7,7,difficulty="medium")
            if tid == TARGETS[0]:
                override = gen.generate(7,7,difficulty="medium",n_components=5)
                report["ignored_override"] = {"seed":7,"sample_index":7,"difficulty":"medium","overrides":{"n_components":5},
                    "input":override,"equals_no_override":override==base,"observed_components":len(components(override)),
                    "self_check":gen.self_check(override),"racket_output":bridge.eval_text(rule_application(rules[tid],override))}
                report["declared_axis_boundary"] = []
                for value in (8,14):
                    try:
                        gen.generate(7,7,difficulty="medium",grid_h=value)
                        outcome = "accepted"
                    except Exception as exc:
                        outcome = type(exc).__name__+": "+str(exc)
                    report["declared_axis_boundary"].append({"grid_h":value,"result":outcome})
                report["empty_grid_self_check"] = gen.self_check([[0]*9 for _ in range(9)])
                report["canonical_component_sizes"] = sorted({len(cells) for pair in records[tid]["train"] for color,cells in components(pair["input"])})
            else:
                grid = [[0]*9 for _ in range(8)]
                grid[0][0],grid[0][2]=2,3
                grid[2][0]=2
                for r,c in ((5,4),(5,5),(6,4)):
                    grid[r][c]=2
                grid[2][7]=grid[3][7]=3
                reference = bridge.eval_text(rule_application(rules[tid],grid))
                report["largest_counterexample"] = {"input":grid,"self_check":gen.self_check(grid),
                    "racket_output":reference,"largest_python":gallery(grid,True),"first_object_rival":gallery(grid,False),
                    "rival_fits_canonical_train":[gallery(p["input"],False)==p["output"] for p in records[tid]["train"]]}
                report["degenerate_failures"] = []
                for texture in gen.DEGENERATE_TEXTURES:
                    grid = gen.generate(7,7,difficulty="medium",texture=texture)
                    item = {"texture":texture,"input":grid,"self_check":gen.self_check(grid)}
                    try:
                        item["racket_output"] = bridge.eval_text(rule_application(rules[tid],grid))
                    except Exception as exc:
                        item["racket_error"] = type(exc).__name__+": "+str(exc)
                    report["degenerate_failures"].append(item)
            save(out / (tid+".json"),report)
            print(tid, 'draws=',report['default_draws'],'racket=',report['default_racket_checked'],'failures=',report['default_failures'])
        return 0
    finally:
        bridge.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True)
    parser.add_argument('--count',type=int,default=80)
    parser.add_argument('--in-runtime',action='store_true')
    args=parser.parse_args()
    if args.in_runtime:
        return execute(args)
    library=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(library/'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-audit-probe-') as temp:
        root=Path(temp)
        prepare_runtime(Catalog(library),root,task_ids=list(TARGETS))
        script=root/'audit_probe.py'; shutil.copy2(__file__,script)
        cmd=[sys.executable,str(script),'--in-runtime','--out',str(out),'--count',str(args.count)]
        env=dict(os.environ,PYTHONPATH=str(root),PYTHONNOUSERSITE='1'); env.pop('PYTHONHOME',None)
        result=subprocess.run(cmd,cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/'run.log').write_text(result.stdout)
        save(out/'runtime.json',{'argv':cmd,'cwd':str(root),'exit_code':result.returncode,'targets':list(TARGETS)})
        print(result.stdout)
        return result.returncode


if __name__=='__main__':
    raise SystemExit(main())
