#!/usr/bin/env python3
"""Findings-only, reproducible checks for this packet's two assigned audits."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

TARGETS = ("f9cd85012aa8", "926c6bd137d3")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def colour_components(grid, colour):
    todo = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == colour}
    groups = []
    while todo:
        start = min(todo)
        todo.remove(start)
        cells, stack = {start}, [start]
        while stack:
            r, c = stack.pop()
            for p in ((r-1,c), (r+1,c), (r,c-1), (r,c+1)):
                if p in todo:
                    todo.remove(p); cells.add(p); stack.append(p)
        groups.append(cells)
    return groups


def frame_rival(grid, *, erase_exterior):
    output = copy.deepcopy(grid)
    covered = set()
    for cells in colour_components(grid, 4):
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        markers = [grid[r][c] for r in range(r0+1, r1) for c in range(c0+1, c1) if grid[r][c] not in (0,4)]
        if not markers:
            raise ValueError("frame without interior marker")
        for r in range(r0, r1+1):
            for c in range(c0, c1+1):
                covered.add((r,c))
                if grid[r][c] == 0:
                    output[r][c] = markers[0]
    if erase_exterior:
        for r, row in enumerate(grid):
            for c in range(len(row)):
                if (r,c) not in covered:
                    output[r][c] = 0
    return output


def bbox_rival(grid):
    cells = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    r0,r1 = min(r for r,c in cells),max(r for r,c in cells)
    c0,c1 = min(c for r,c in cells),max(c for r,c in cells)
    return [[6 if r0<=r<=r1 and c0<=c<=c1 else 0 for c in range(len(grid[0]))] for r in range(len(grid))]


def worker(args):
    sys.path.insert(0,str(Path.cwd()))
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash
    from scripts.rule_smoke import rule_application
    from arc_repl.racket_bridge import RacketBridge
    bridge = RacketBridge(max_calls_before_restart=500)
    any_failures = False
    try:
        for tid in TARGETS:
            gen = importlib.import_module(f"puzzle_generators.per_puzzle.{tid}.generator")
            source = canonical_rule_source(tid)
            report = dict(task_id=tid,generator_sha256=digest(gen.__file__),
                          rule_sha256=hashlib.sha256(source.encode()).hexdigest(),
                          normalized_rule_hash=normalized_rule_hash(source),
                          runtime_directory=str(Path.cwd()), findings=[], failures=[])
            def oracle(g):
                return bridge.eval_text(rule_application(source,g))
            if tid == TARGETS[0]:
                overrides = dict(grid_h=5, grid_w=6, shape_size=3, n_distractor=0)
                grid = gen.generate(0,101,difficulty="medium",**overrides)
                baseline = gen.generate(0,101,difficulty="medium")
                observed = dict(grid_h=len(grid),grid_w=len(grid[0]),
                                shape_size=sum(v==6 for row in grid for v in row),
                                n_distractor=len({v for row in grid for v in row if v not in (0,6)}))
                actual = oracle(grid)
                report["findings"].append(dict(id="A1.1",classification="reproduced override defect",
                    seed=0,sample_index=101,difficulty="medium",overrides=overrides,observed=observed,
                    same_as_no_overrides=grid==baseline,validator_errors=gen.self_check(grid,meta={"overrides":overrides}),
                    belongs_to_documented_generator_domain=True,input=grid,actual_racket_output=actual,
                    rival_name="bbox_of_all_nonzero_not_just_6",rival_output=bbox_rival(grid)))
                samples=failures=refuted=0
                canonical = canonical_pairs(tid)
                report["canonical_inputs"] = len(canonical)
                report["canonical_validator_rejections"] = [i for i,p in enumerate(canonical) if gen.self_check(p["input"])]
                for seed in range(16):
                    for band in ("easy","medium","hard"):
                        g=gen.generate(seed,101+seed,difficulty=band)
                        samples+=1
                        if gen.self_check(g):failures+=1
                        if bbox_rival(g)!=oracle(g):refuted+=1
                report["ordinary_census"] = dict(seed_range=[0,15],sample_index="101+seed",bands=["easy","medium","hard"],
                    samples=samples,validator_failures=failures,bbox_all_nonzero_rival_refuted=refuted)
                if observed == overrides or grid != baseline:
                    report["failures"].append("Expected ignored-axis reproducer changed; inspect rather than quote stale finding")
            else:
                samples=agrees=mirror_errors=0
                marker_colours=set()
                canonical=canonical_pairs(tid)
                canonical_mismatches=[]
                for i,pair in enumerate(canonical):
                    actual=oracle(pair["input"])
                    if actual!=pair["output"]:
                        report["failures"].append(dict(kind="canonical_label_disagrees_with_racket",index=i))
                    rival=frame_rival(pair["input"],erase_exterior=True)
                    if rival!=actual:
                        canonical_mismatches.append(i)
                        if not report.get("canonical_counterexample"):
                            report["canonical_counterexample"] = dict(index=i,input=pair["input"],actual_racket_output=actual,
                                rival_name="fill_frames_then_erase_exterior",rival_output=rival,
                                validator_errors=gen.self_check(pair["input"]),belongs_to_documented_task_domain=True,
                                belongs_to_emitted_generator_support=False)
                for seed in range(32):
                    for band in ("easy","medium","hard"):
                        g=gen.generate(seed,101+seed,difficulty=band)
                        actual=oracle(g);samples+=1
                        agrees+=frame_rival(g,erase_exterior=True)==actual
                        mirror_errors+=frame_rival(g,erase_exterior=False)!=actual
                        marker_colours.update(v for row in g for v in row if v not in (0,4))
                report["findings"].append(dict(id="A2.1",classification="reproduced generator support gap",
                    rival="fill_frames_then_erase_exterior",seed_range=[0,31],sample_index="101+seed",
                    bands=["easy","medium","hard"],generated=samples,rival_matches=agrees,
                    control_mirror_mismatches=mirror_errors,canonical_pairs=len(canonical),
                    canonical_rival_mismatch_indices=canonical_mismatches,observed_marker_colours=sorted(marker_colours)))
                mismatches=[]
                for seed in range(64):
                    g=gen.generate(seed,101+seed,difficulty="hard",n_frames=4)
                    count=len(colour_components(g,4))
                    if count!=4:
                        mismatches.append(dict(seed=seed,sample_index=101+seed,observed=count))
                        if "frame_count_counterexample" not in report:
                            report["frame_count_counterexample"] = dict(seed=seed,sample_index=101+seed,difficulty="hard",
                                overrides={"n_frames":4},input=g,actual_racket_output=oracle(g),
                                rival_name="fill_frames_then_erase_exterior",rival_output=frame_rival(g,erase_exterior=True),
                                validator_errors=gen.self_check(g,meta={"overrides":{"n_frames":4}}),
                                belongs_to_documented_generator_domain=True,observed_n_frames=count)
                report["findings"].append(dict(id="A2.2",classification="reproduced silent count shortfall",
                    seed_range=[0,63],sample_index="101+seed",difficulty="hard",overrides={"n_frames":4},
                    samples=64,mismatches=mismatches))
                # An invalid input with a marker moved OUTSIDE the frame still
                # passes the supplied validator; it is not a generated-domain claim.
                g=gen.generate(0,101,difficulty="easy")
                moved=copy.deepcopy(g)
                for r,row in enumerate(moved):
                    for c,v in enumerate(row):
                        if v not in (0,4):moved[r][c]=0
                frame=colour_components(g,4)[0]
                r0,r1=min(r for r,c in frame),max(r for r,c in frame)
                c0,c1=min(c for r,c in frame),max(c for r,c in frame)
                outside=next((r,c) for r,row in enumerate(moved) for c,v in enumerate(row)
                             if not (r0<=r<=r1 and c0<=c<=c1))
                moved[outside[0]][outside[1]]=1
                try:
                    actual=oracle(moved);error=None
                except Exception as exc:
                    actual=None;error=str(exc)
                report["findings"].append(dict(id="A2.3",classification="validator accepts invalid domain",
                    seed=0,sample_index=101,difficulty="easy",mutation="move sole marker outside its frame",
                    input=moved,validator_errors=gen.self_check(moved),actual_racket_output=actual,racket_error=error,
                    rival_output=None,belongs_to_documented_generator_domain=False))
                if not all((samples==agrees,canonical_mismatches,not mirror_errors,mismatches,error)):
                    report["failures"].append("An expected audit finding did not reproduce; inspect report")
            any_failures = any_failures or bool(report["failures"])
            path=args.out/f"{tid}.json"
            path.write_text(json.dumps(report,indent=2)+"\n")
            print(tid,[(x["id"],x["classification"]) for x in report["findings"]],"audit errors:",len(report["failures"]))
    finally:
        bridge.close()
    return int(any_failures)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--worker",action="store_true")
    args=parser.parse_args();args.out=args.out.resolve();args.out.mkdir(parents=True,exist_ok=True)
    if args.worker:return worker(args)
    repo=Path(__file__).resolve().parents[3];sys.path.insert(0,str(repo/"src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime,run_process
    with tempfile.TemporaryDirectory(prefix="arcpuzzles-audits-") as directory:
        runtime=Path(directory);prepare_runtime(Catalog(repo),runtime,task_ids=list(TARGETS))
        shutil.copy2(__file__,runtime/"audit_assigned.py")
        run=run_process([sys.executable,"audit_assigned.py","--worker","--out",str(args.out)],runtime,timeout=600)
        run["cwd"]=str(runtime);(args.out/"execution.json").write_text(json.dumps(run,indent=2)+"\n")
        print(run["stdout"]);print(run["stderr"],file=sys.stderr)
        return run["exit_code"] if not run["timed_out"] else 124


if __name__=="__main__":raise SystemExit(main())
