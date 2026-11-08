"""Findings-only, source-bound probes for this packet's two audit targets.

This script never edits an audited generator. It uses a relocated runtime and
actual Racket outputs; finite competitors are diagnostics, not label sources.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

TARGETS = ("d414585aa873", "4199aa353fa1")


def hash_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rectangle_rule(grid, order=(2, 1)):
    out = copy.deepcopy(grid)
    for color in order:
        points = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == color]
        if len(points) != 2:
            continue
        (r1,c1), (r2,c2) = points
        r1,r2 = sorted((r1,r2)); c1,c2 = sorted((c1,c2))
        for r in range(r1,r2+1):
            for c in range(c1,c2+1):
                if r in (r1,r2) or c in (c1,c2):
                    out[r][c] = 3 if color == 2 else 8
    return out


def normalized(points):
    r0,c0 = min(r for r,c in points), min(c for r,c in points)
    return sorted((r-r0,c-c0) for r,c in points)


def rotated(points):
    return normalized([(c,-r) for r,c in points])


def stamp_rule(grid, wrong_control=None):
    controls = [v for v in (2,3,4,6) if any(v in row for row in grid)]
    control = controls[0] if controls else 2
    times = {2:0,3:1,4:2,6:3}[control]
    if control == wrong_control:
        times = (times+1) % 4
    points = normalized([(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 1])
    for _ in range(times):
        points = rotated(points)
    ar,ac = next((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 7)
    out = [[0]*len(grid[0]) for row in grid]
    for r,c in points:
        if 0 <= ar+r < len(out) and 0 <= ac+c < len(out[0]):
            out[ar+r][ac+c] = 8
    return out


def literal(grid):
    return "'(" + " ".join("(" + " ".join(map(str,row)) + ")" for row in grid) + ")"


def run(args, runtime):
    repo = args.repo.resolve()
    sys.path.insert(0, str(runtime))
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    tasks = {d["task_id"]:d for d in map(json.loads,(repo / "shared/data/canonical/puzzles.jsonl").open()) if d["task_id"] in TARGETS}
    bridge = RacketBridge(timeout=20)
    report = {"schema":"two-target-audit-v1", "runtime_directory":str(runtime),
              "command":{"cwd":"repo", "argv":["python3",*sys.argv]},
              "sample_domain":{"bands":["easy","medium","hard"],"seed_range_inclusive":[0,args.seeds-1],"sample_index_range_inclusive":[0,args.samples-1]},
              "targets":{}}
    try:
        for tid in TARGETS:
            source = repo / f"generators/{tid}/generator.py"
            gen = load(source, "audit_"+tid)
            task = tasks[tid]
            rule = task["program_solution"]
            wrapped = wrap_rule(rule)
            identity = {"task_id":tid, "generator_sha256":hash_bytes(source.read_bytes()), "rule_sha256":hash_bytes(rule.encode())}
            result = {**identity, "canonical":[], "counts":{}, "manifest":[], "failures":[], "witnesses":{}}
            counts = Counter(); unique = set()
            def actual(grid):
                output = bridge.eval_text(f"({wrapped} {literal(grid)})")
                if not isinstance(output,list) or not output or not all(isinstance(row,list) for row in output):
                    raise RuntimeError(f"Racket did not return a grid: {output!r}")
                return output
            def witness(grid, output, rival, location, **extra):
                errors = gen.self_check(grid)
                return {**identity, **location, "input":grid, "racket_output":output, "rival_output":rival,
                        "validator_errors":errors, "command":report["command"], **extra}
            for split in ("train","test"):
                pairs = task.get(split, [])
                if isinstance(pairs,dict):pairs = [pairs]
                for index,pair in enumerate(pairs):
                    grid = [[int(v) for v in row] for row in pair["input"]]
                    expected = [[int(v) for v in row] for row in pair["output"]]
                    output = actual(grid); errors = gen.self_check(grid)
                    row = {"split":split,"index":index,"validator_errors":errors,"racket_matches_stored":output==expected}
                    if tid == TARGETS[0]:
                        rival = rectangle_rule(grid,(1,2))
                        row["reverse_paint_order_changes_answer"] = rival != output
                        if rival != output and "canonical_overlap" not in result["witnesses"]:
                            result["witnesses"]["canonical_overlap"] = witness(grid,output,rival,{"source":"canonical","split":split,"index":index,"seed":None,"sample_index":None,"overrides":{}},in_documented_generator_domain=False)
                    if output != expected:result["failures"].append({"kind":"canonical_parity",**row})
                    result["canonical"].append(row)
            for band in ("easy","medium","hard"):
                for seed in range(args.seeds):
                    episode = []
                    for index in range(args.samples):
                        loc = {"difficulty":band,"seed":seed,"sample_index":index,"overrides":{}}
                        try:
                            grid = gen.generate(seed,index,difficulty=band)
                            errors = gen.self_check(grid); output = actual(grid)
                            mirror = rectangle_rule(grid) if tid == TARGETS[0] else stamp_rule(grid)
                            if mirror != output:result["failures"].append({"kind":"mirror_parity",**loc,"input":grid,"racket_output":output,"mirror_output":mirror})
                            if errors:result["failures"].append({"kind":"generated_self_check",**loc,"errors":errors})
                            counts["generated_draws"] += 1; counts["validator_accepted"] += not bool(errors)
                            raw=json.dumps(grid,separators=(",",":")).encode(); ih=hash_bytes(raw);unique.add(ih)
                            result["manifest"].append({**loc,"input_sha256":ih,"output_sha256":hash_bytes(json.dumps(output,separators=(",",":")).encode())})
                            if tid == TARGETS[0]:
                                counts["reverse_paint_order_changes_answer"] += rectangle_rule(grid,(1,2)) != output
                            else:
                                shape=normalized([(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==1])
                                counts["quarter_turn_symmetric_templates"] += rotated(shape)==shape
                                counts["half_turn_symmetric_templates"] += rotated(rotated(shape))==shape
                                counts["three_cell_templates"] += len(shape)==3
                                episode.append({"input":grid,"output":output,"location":loc})
                        except Exception as exc:
                            result["failures"].append({"kind":"execution",**loc,"error":str(exc)})
                    if tid==TARGETS[1] and len(episode)==args.samples:
                        for start in range(args.samples-4):
                            demos,query=episode[start:start+4],episode[start+4]
                            counts["overlapping_four_demo_query_windows"] += 1
                            survivors=[control for control in (2,3,4,6)
                                if all(stamp_rule(p["input"],control)==p["output"] for p in demos)
                                and stamp_rule(query["input"],control)!=query["output"]]
                            if survivors:
                                counts["query_changing_unrefuted_control_windows"] += 1
                                if "unidentified_control" not in result["witnesses"]:
                                    control=survivors[0]
                                    result["witnesses"]["unidentified_control"] = witness(query["input"],query["output"],stamp_rule(query["input"],control),query["location"],in_documented_generator_domain=True,wrong_control=control,rival_definition="Add one clockwise quarter-turn only for this control; use intended mapping for all others.",demos=demos)
            if tid==TARGETS[0]:
                # Reproduce one ignored-axis claim without changing audited code.
                for index in range(20):
                    grid=gen.generate(0,index,difficulty="medium",rect_min_h=6)
                    heights=[]
                    for color in (1,2):
                        rs=[r for r,row in enumerate(grid) for v in row if v==color]
                        heights.append(max(rs)-min(rs)+1)
                    if min(heights)<6:
                        result["witnesses"]["ignored_rect_min_h"] = witness(grid,actual(grid),None,{"difficulty":"medium","seed":0,"sample_index":index,"overrides":{"rect_min_h":6}},in_documented_generator_domain=True,observed_rectangle_heights=heights)
                        break
            else:
                grid=gen.generate(0,0,difficulty="medium")
                bad=[[0 if v==7 else v for v in row] for row in grid]
                entry=witness(bad,None,None,{"source":"mutated_generated_input","difficulty":"medium","seed":0,"sample_index":0,"overrides":{},"mutation":"remove the color-7 anchor"},in_documented_generator_domain=False)
                try:entry["racket_output"]=actual(bad)
                except Exception as exc:entry["racket_error"]={"type":type(exc).__name__,"message":str(exc)}
                result["witnesses"]["missing_anchor_passes_validator"]=entry
            result["counts"]={**counts,"unique_inputs":len(unique)}
            report["targets"][tid]=result
    finally:
        bridge.close()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({tid:{"counts":r["counts"],"unexpected_failures":len(r["failures"]),"witnesses":list(r["witnesses"])} for tid,r in report["targets"].items()},indent=2))
    return int(any(r["failures"] for r in report["targets"].values()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,default=Path("repo"))
    parser.add_argument("--seeds",type=int,default=20)
    parser.add_argument("--samples",type=int,default=10)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.seeds<1 or args.samples<5:parser.error("positive seeds and at least 5 samples required")
    sys.path.insert(0,str(args.repo.resolve()/"src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix="arc-audit-probes-") as directory:
        runtime=Path(directory)
        prepare_runtime(Catalog(args.repo.resolve()),runtime,task_ids=list(TARGETS))
        return run(args,runtime)


if __name__=="__main__":
    raise SystemExit(main())
