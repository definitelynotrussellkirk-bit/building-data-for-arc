"""Reproducible census and real-Racket counterexample replay for M93.

Run via the packet's run_with_racket.py. Outputs are research evidence, not
an admission/approval record. A --source file supports frozen-baseline replay.
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
import types

TASK = "d68b3843203e"
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared/runtime"))
# The source tree stores the staged runtime's `scripts` namespace in shared/tools.
# Bind only this checkout; never borrow a sibling repository or installation.
scripts = types.ModuleType("scripts")
scripts.__path__ = [str(REPO / "shared/tools")]
sys.modules.setdefault("scripts", scripts)
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def normalize_grid(grid):
    """Accept the catalog's integer rows or compact ASCII-digit rows."""
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must have nonempty rows")
    rows = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(char not in "0123456789" for char in row):
                raise ValueError("compact rows must contain ASCII ARC digits")
            row = [int(char) for char in row]
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError("grid rows must be nonempty sequences")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("cells must be literal ARC integers 0..9")
        rows.append(list(row))
    if any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("grid must be rectangular")
    return rows


def read_task(task_id):
    with (REPO / "shared/data/canonical/puzzles.jsonl").open() as stream:
        rows = [row for line in stream if (row := json.loads(line)).get("task_id") == task_id]
    if len(rows) != 1:
        raise ValueError(f"Expected one canonical row for {task_id}, got {len(rows)}")
    task = rows[0]
    for split in ("train", "test"):
        pairs = task[split]
        if isinstance(pairs, dict):
            pairs = [pairs]
            task[split] = pairs
        if not isinstance(pairs, list):
            raise ValueError(f"{task_id} {split} must be a pair or pair list")
        for pair in pairs:
            for side in ("input", "output"):
                pair[side] = normalize_grid(pair[side])
    return task


def load_generator(source):
    spec = importlib.util.spec_from_file_location("probe_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scan_frames(grid):
    """Independent exhaustive border enumeration, rejecting attached yellow cells."""
    h,w = len(grid),len(grid[0])
    frames = []
    for r0 in range(h-2):
        for c0 in range(w-2):
            if grid[r0][c0] != 4:
                continue
            for r1 in range(r0+2,h):
                for c1 in range(c0+2,w):
                    border = {(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)
                              if r in (r0,r1) or c in (c0,c1)}
                    if not all(grid[r][c] == 4 for r,c in border):
                        continue
                    if any(grid[nr][nc] == 4 and (nr,nc) not in border
                           for r,c in border for nr,nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1))
                           if 0 <= nr < h and 0 <= nc < w):
                        continue
                    inside = [(r,c) for r in range(r0+1,r1) for c in range(c0+1,c1)]
                    markers = {(r,c) for r,c in inside if grid[r][c] == 2}
                    adjacent = any((r+1,c) in markers or (r,c+1) in markers for r,c in markers)
                    frames.append({"box":[r0,c0,r1,c1], "interior":inside,
                                   "count":len(markers), "adjacent":adjacent})
    return frames


def scene_profile(grid, facts=None):
    """Return the task-level frame count and exterior cue-cell count.

    Generated and canonical inputs reserve colors 5..9 for the detached cue,
    so counting those cells is independent of the generator implementation.
    """
    facts = scan_frames(grid) if facts is None else facts
    cue_size = sum(value in range(5, 10) for row in grid for value in row)
    return len(facts), cue_size


def oracle_and_rival(grid, facts=None):
    expected, rival = copy.deepcopy(grid), copy.deepcopy(grid)
    for fact in facts if facts is not None else scan_frames(grid):
        color = 8 if fact["adjacent"] else (7 if fact["count"] >= 2 else 6)
        for r,c in fact["interior"]:
            expected[r][c] = 5 + fact["count"]
            rival[r][c] = color
    return expected,rival


def rule_application(rule, grid):
    literal = "'(" + " ".join("("+" ".join(map(str,row))+")" for row in grid) + ")"
    return f"({wrap_rule(rule)} {literal})"


def rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def census(module, seed, per_band):
    counts = Counter()
    shapes = Counter()
    nframes = Counter()
    cue_sizes = Counter()
    joint_profiles = Counter()
    colors = Counter()
    examples = {}
    records = []
    for band in (None,"easy","medium","hard"):
        for index in range(per_band):
            grid = module.generate(seed,index,difficulty=band)
            facts = scan_frames(grid)
            expected,rival = oracle_and_rival(grid,facts)
            reasons = module.self_check(grid)
            if reasons:
                raise AssertionError({"band":band,"index":index,"self_check":reasons})
            assert facts and expected != grid
            label = "default" if band is None else band
            record = {"difficulty":band,"seed":seed,"sample_index":index,
                      "input":grid,"independent_output":expected,"rival_output":rival}
            records.append(record)
            n_frames, cue_size = scene_profile(grid, facts)
            nframes[str(n_frames)] += 1
            cue_sizes[str(cue_size)] += 1
            joint_profiles[f"{n_frames}_frames/{cue_size}_cue_cells"] += 1
            for f in facts:
                r0,c0,r1,c1 = f["box"]
                shapes[f"{r1-r0+1}x{c1-c0+1}"] += 1
                colors[str(5+f["count"])] += 1
            observed = {
                "touching_pair": any(f["count"]==2 and f["adjacent"] for f in facts),
                "separated_three": any(f["count"]==3 and not f["adjacent"] for f in facts),
                "repeated_counts": len({f["count"] for f in facts}) < len(facts),
                "thin_frame": any(3 in (f["box"][2]-f["box"][0]+1,f["box"][3]-f["box"][1]+1) for f in facts),
                "edge_frame": any(f["box"][0]==0 or f["box"][1]==0 or f["box"][2]==len(grid)-1 or f["box"][3]==len(grid[0])-1 for f in facts),
                "shortcut_refuted": expected != rival,
            }
            for key, hit in observed.items():
                counts[f"{label}/{key}"] += int(hit)
                counts[f"all/{key}"] += int(hit)
                if hit and key not in examples:
                    examples[key] = dict(record)
    return {"draws":len(records),"per_band":per_band,"seed":seed,
            "witness_counts":dict(sorted(counts.items())),
            "frame_number_histogram":dict(sorted(nframes.items())),
            "cue_size_histogram":dict(sorted(cue_sizes.items())),
            "frame_cue_joint_histogram":dict(sorted(joint_profiles.items())),
            "frame_shape_histogram":dict(sorted(shapes.items())),
            "fill_color_histogram":dict(sorted(colors.items())),
            "distinct_inputs":len({json.dumps(x["input"]) for x in records})}, records, examples


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=REPO / f"generators/{TASK}/generator.py")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--per-band", type=int, default=120)
    p.add_argument("--seed", type=int, default=811)
    p.add_argument("--racket-per-band", type=int, default=60)
    args = p.parse_args()
    if args.per_band < 1 or not 0 <= args.racket_per_band <= args.per_band:
        p.error("require per-band >= 1 and 0 <= racket-per-band <= per-band")
    args.out.mkdir(parents=True,exist_ok=False)
    module = load_generator(args.source)
    report, records, examples = census(module,args.seed,args.per_band)
    task = read_task(TASK)
    canonical = task["train"] + task["test"]
    canonical_profiles = Counter(scene_profile(pair["input"]) for pair in canonical)
    canonical_frame_counts = Counter(str(profile[0]) for profile in canonical_profiles.elements())
    canonical_cue_sizes = Counter(str(profile[1]) for profile in canonical_profiles.elements())
    report.update({"task_id":TASK,"generator_sha256":hashlib.sha256(args.source.read_bytes()).hexdigest(),
                   "version":module.VERSION,
                   "rule_sha256":hashlib.sha256(task["program_solution"].encode()).hexdigest(),
                   "canonical_pairs":len(canonical),
                   "canonical_frame_number_histogram":dict(sorted(canonical_frame_counts.items())),
                   "canonical_cue_size_histogram":dict(sorted(canonical_cue_sizes.items())),
                   "canonical_frame_cue_joint_histogram":{
                       f"{frames}_frames/{cue}_cue_cells": count
                       for (frames, cue), count in sorted(canonical_profiles.items())
                   },
                   "canonical_shortcut_matches":sum(oracle_and_rival(p["input"])[1]==p["output"] for p in canonical),
                   "canonical_self_check_rejections":sum(bool(module.self_check(p["input"])) for p in canonical)})
    checked, metamorphic = 0,0
    cases = []
    with RacketBridge() as bridge:
        for pair in canonical:
            output = bridge.eval_text(rule_application(task["program_solution"],pair["input"]))
            assert output == pair["output"] == oracle_and_rival(pair["input"])[0]
            checked += 1
            # Each of the eight D4 orientations must preserve frame-local counts.
            for reflected in (False,True):
                inp = [row[::-1] for row in pair["input"]] if reflected else copy.deepcopy(pair["input"])
                out = [row[::-1] for row in pair["output"]] if reflected else copy.deepcopy(pair["output"])
                for _ in range(4):
                    assert bridge.eval_text(rule_application(task["program_solution"],inp)) == out
                    metamorphic += 1
                    inp,out = rotate(inp),rotate(out)
        for record in records:
            if record["sample_index"] >= args.racket_per_band:
                continue
            actual = bridge.eval_text(rule_application(task["program_solution"],record["input"]))
            assert actual == record["independent_output"], record
            if hasattr(module,"rule_mirror"):
                assert actual == module.rule_mirror(record["input"]), record
            checked += 1
        for name,record in sorted(examples.items()):
            actual = bridge.eval_text(rule_application(task["program_solution"],record["input"]))
            assert actual == record["independent_output"]
            cases.append({"name":name,**record,"racket_output":actual})
        report["runtime_identity"] = bridge.runtime_identity
    report["racket_exact_matches"] = checked
    report["racket_generated_cases"] = checked-len(canonical)
    report["racket_metamorphic_matches"] = metamorphic
    report["counterexample_cases_replayed"] = len(cases)
    (args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    (args.out/"counterexamples.json").write_text(json.dumps(cases,indent=2)+"\n")
    (args.out/"sampled_cases.jsonl").write_text("".join(json.dumps(r,separators=(",",":"))+"\n" for r in records))
    print(json.dumps({k:v for k,v in report.items() if k != "runtime_identity"},indent=2))


if __name__ == "__main__":
    main()
