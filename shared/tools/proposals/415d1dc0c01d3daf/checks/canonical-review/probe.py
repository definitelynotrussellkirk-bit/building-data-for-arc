#!/usr/bin/env python3
"""Finite, read-only contract probes for the selected d89cff1052a2 source."""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[2] / "repo"
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "generators/d89cff1052a2/generator.py"
sys.path[:0] = [str(ROOT / "shared/runtime"), str(ROOT / "src")]
spec = importlib.util.spec_from_file_location("reviewed_d89cff1052a2", SOURCE)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(grid):
    return tuple(tuple(row) for row in grid)


def check_grid(grid, overrides):
    errors = []
    h, w = len(grid), len(grid[0])
    if not (3 <= h <= 15 and 3 <= w <= 30):
        errors.append("dimension bounds")
    if not all(isinstance(row, list) and len(row) == w for row in grid):
        errors.append("rectangular list rows")
    flat = [cell for row in grid for cell in row]
    if any(type(cell) is not int or not 0 <= cell <= 9 for cell in flat):
        errors.append("literal integer palette")
    counts = Counter(flat)
    if not 2 <= len(counts) <= 4 or min(counts.values()) < 2:
        errors.append("exact palette support")
    observed = {"grid_h": h, "grid_w": w, "palette_size": len(counts),
                "ud_asymmetric": grid != list(reversed(grid))}
    if any(observed[k] != v for k, v in overrides.items() if v is not None):
        errors.append("independent override observation")
    if gen.observe_overrides(grid) != observed:
        errors.append("reported override observation")
    before = key(grid)
    errors.extend(gen.self_check(grid, meta={"overrides": overrides}))
    if key(grid) != before:
        errors.append("self_check mutated input")
    return errors


def main():
    started = time.monotonic()
    report = {
        "schema": "arcpuzzles-focused-canonical-review-v1",
        "task_id": gen.TASK_ID,
        "cwd": str(Path.cwd()),
        "argv": sys.argv,
        "source_sha256": digest(SOURCE),
        "source_path": str(SOURCE.relative_to(ROOT)),
        "support_hashes": {
            name: digest(ROOT / name) for name in (
                "shared/runtime/puzzle_generators/base.py",
                "src/arcpuzzles/worker.py",
                "generators/d89cff1052a2/tests/test_generator.py",
                "generators/d89cff1052a2/notes.md",
                "generators/d89cff1052a2/evidence/review_index.json",
            )
        },
        "rule_hash": gen.RULE_HASH,
        "checks": {}, "failures": [],
        "limits": [
            "Finite deterministic probes, not a proof over all seeds and indices.",
            "This script checks generated inputs, not fresh Racket authority execution.",
            "No prior solve files or historical solve programs were consulted.",
        ],
    }
    count = 0
    for difficulty, h, w, palette_size, asymmetric in itertools.product(
            (None, "easy", "medium", "hard"), range(3, 16), range(3, 31),
            range(2, 5), (False, True)):
        overrides = dict(grid_h=h, grid_w=w, palette_size=palette_size,
                         ud_asymmetric=asymmetric)
        grid = gen.generate(71, 11, difficulty=difficulty, **overrides)
        errors = check_grid(grid, overrides)
        count += 1
        if errors:
            report["failures"].append(dict(kind="joint_overrides", seed=71,
                sample_index=11, difficulty=difficulty, overrides=overrides,
                errors=errors, input=grid))
    report["checks"]["joint_overrides"] = dict(samples=count, seed=71,
        sample_index=11, difficulty=[None,"easy","medium","hard"],
        grid_h=[3,15], grid_w=[3,30], palette_size=[2,4],
        ud_asymmetric=[False,True], failures=len(report["failures"]))

    count = 0
    rotations = 0
    seeds = (0, 1, 17, 71, 1234, -17)
    for difficulty, seed in itertools.product((None,"easy","medium","hard"), seeds):
        grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(12)]
        for index, grid in enumerate(grids):
            errors = check_grid(grid, {})
            if grid == list(reversed(grid)):
                errors.append("default flip is invisible")
            if len(grid) == 3 if index % 2 else len(grid) != 3:
                errors.append("default schedule mismatch")
            if grid != gen.generate(seed,index,difficulty=difficulty,
                    grid_h=None,grid_w=None,palette_size=None,ud_asymmetric=None):
                errors.append("None override changed default draw")
            if grid != gen.generate(seed,index,difficulty=difficulty):
                errors.append("nondeterministic generation")
            if errors:
                report["failures"].append(dict(kind="default",seed=seed,
                    sample_index=index,difficulty=difficulty,errors=errors,input=grid))
            count += 1
        for start in range(9):
            lesson = grids[start:start+4]
            for heldout in range(4):
                demos = [g for i,g in enumerate(lesson) if i != heldout]
                if not any(len(g) != 3 for g in demos):
                    report["failures"].append(dict(kind="contiguous_rotation",seed=seed,
                        sample_index=start,difficulty=difficulty,heldout=heldout))
                rotations += 1
    report["checks"]["default_schedule"] = dict(samples=count, seeds=list(seeds),
        sample_indices=[0,11], starts=[0,8], rotations=rotations,
        difficulty=[None,"easy","medium","hard"],
        checks=["all colors supported", "self_check", "observable axes",
                "repeatability", "null overrides", "asymmetry", "query holdouts"])

    # The production worker rejects duplicate input/output pairs before assigning
    # the first three accepted pairs to train. A repeated broad slot can therefore
    # invalidate the stronger every-query-rotation statement, even though raw
    # sample indices alternate perfectly. Search only one short fixed window.
    searched = 0
    collision = None
    for seed in range(25000):
        a = gen.generate(seed,1,difficulty="easy")
        b = gen.generate(seed,3,difficulty="easy")
        searched += 1
        if a == b:
            seen = set()
            accepted = []
            rejected = []
            for index in range(20):
                grid = gen.generate(seed,index,difficulty="easy")
                if key(grid) in seen:
                    rejected.append(index)
                    continue
                seen.add(key(grid))
                accepted.append({"sample_index":index,"input":grid})
                if len(accepted) == 4:
                    break
            collision = dict(seed=seed,sample_index=0,difficulty="easy",overrides={},
                duplicate_sample_indices=[1,3],rejected_indices=rejected,
                accepted=accepted,accepted_heights=[len(row["input"]) for row in accepted])
            collisions = []
            for heldout in range(4):
                demos = [row["input"] for i,row in enumerate(accepted) if i != heldout]
                if all(len(grid)==3 for grid in demos):
                    collisions.append(heldout)
            collision["ambiguous_holdout_positions"] = collisions
            break
    report["checks"]["duplicate_broad_slot_search"] = dict(
        search_seeds=[0,searched-1],searched_seeds=searched,
        sample_indices=[1,3],difficulty="easy",overrides={},collision=collision)
    report["elapsed_seconds"] = round(time.monotonic()-started,6)
    report["exit_code"] = 0 if not report["failures"] else 1
    output = OUT / "probe.json"
    output.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"report":str(output),"joint_samples":8736,
        "default_samples":count,"failures":len(report["failures"]),
        "searched_seeds":searched,
        "collision_seed":None if collision is None else collision["seed"],
        "elapsed_seconds":report["elapsed_seconds"]},indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
