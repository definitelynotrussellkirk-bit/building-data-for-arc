"""Source-bound, Racket-independent support audit for 1229e88ae0e6.

Run from the packet directory:
  python3 repo/generators/1229e88ae0e6/workspace/review_probe.py \
    --out checks/support_after.json --require-support

Use --generator .review/baseline/repo/generators/1229e88ae0e6/generator.py
for the unchanged source. This audit never creates admitted training labels:
its independent Python specification is NOT a substitute for Racket execution.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Sequence

TASK_ID = "1229e88ae0e6"


def load_generator(library: Path, source: Path):
    sys.path.insert(0, str(library / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("reviewed_centering_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def facts(grid: Sequence[Sequence[int]]) -> dict:
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    r1, c1 = max(r for r, _ in cells), max(c for _, c in cells)
    bh, bw = r1-r0+1, c1-c0+1
    tr, tc = (h-bh)//2, (w-bw)//2
    dr, dc = tr-r0, tc-c0
    movement = ("both_axes" if dr and dc else "vertical_only" if dr else
                "horizontal_only" if dc else "identity")
    return {"shape": [h, w], "bbox_shape": [bh, bw], "origin": [r0, c0],
            "target": [tr, tc], "delta": [dr, dc], "movement": movement,
            "parity": [(h-bh)%2, (w-bw)%2],
            "interior": r0 > 0 and c0 > 0 and r1 < h-1 and c1 < w-1,
            "support": [(r-r0, c-c0) for r, c in cells],
            "colors": sorted({grid[r][c] for r, c in cells}), "cells": cells}


def specification(grid):
    """Independent coordinate specification; does not use generator helpers."""
    a = facts(grid)
    h, w = a["shape"]
    dr, dc = a["delta"]
    out = [[0]*w for _ in range(h)]
    for r, c in a["cells"]:
        out[r+dr][c+dc] = grid[r][c]
    return out


def observed_movement(pair: dict) -> str:
    """Derive the canonical relation from the provided input AND output."""
    a, b = facts(pair["input"]), facts(pair["output"])
    dr, dc = (b["origin"][i]-a["origin"][i] for i in (0, 1))
    return ("both_axes" if dr and dc else "vertical_only" if dr else
            "horizontal_only" if dc else "identity")


def census(module, canonical: dict, seed: int, count: int) -> dict:
    canonical_pairs = canonical["train"] + canonical["test"]
    required = sorted({observed_movement(p) for p in canonical_pairs})
    result = {"schema": "centering-support-audit-v1", "seed": seed,
              "count_per_band": count,
              "label_source": "independent_python_specification_not_Racket",
              "canonical_movement_classes": required, "bands": {}, "failures": []}
    for band in ("easy", "medium", "hard"):
        hist = {k: Counter() for k in ("shape", "bbox_shape", "movement", "parity",
                                      "color_count", "cell_count", "source_origin")}
        supports, inputs, example_by_class = set(), set(), {}
        interior = mirror_errors = validator_errors = rival_killed = windows_failed = 0
        all_grids, all_outputs = [], []
        for i in range(count):
            grid = module.generate(seed, i, difficulty=band)
            a = facts(grid)
            output = specification(grid)
            all_grids.append(grid)
            all_outputs.append(output)
            for key in ("shape", "bbox_shape", "movement", "parity"):
                hist[key][str(a[key])] += 1
            hist["color_count"][str(len(a["colors"]))] += 1
            hist["cell_count"][str(len(a["cells"]))] += 1
            hist["source_origin"][str(a["origin"])] += 1
            supports.add(tuple(a["support"]))
            inputs.add(json.dumps(grid))
            interior += a["interior"]
            mirror_errors += module.rule_mirror(grid) != output
            validator_errors += bool(module.self_check(grid) or module.strict_canonical_like(grid))
            diagonal_only = output if all(a["delta"]) else grid
            rival_killed += diagonal_only != output
            example_by_class.setdefault(a["movement"], {"seed": seed, "sample_index": i,
                "input": grid, "diagnostic_output": output})
        for i in range(max(0, count-module.EXAMPLES_NEEDED)):
            pairs = [{"input": g, "output": o} for g, o in
                     zip(all_grids[i:i+module.EXAMPLES_NEEDED+1],
                         all_outputs[i:i+module.EXAMPLES_NEEDED+1])]
            windows_failed += bool(module.lesson_identifiable(pairs[:-1], pairs[-1]))
        missing = sorted(set(required) - set(hist["movement"]))
        # Match the four-demo export's first-query index instead of only
        # examining a flat/sliding census. Labels remain diagnostic Python.
        query_hist, query_joint = Counter(), Counter()
        for query_seed in range(32):
            query = module.generate(query_seed, module.EXAMPLES_NEEDED, difficulty=band)
            qa = facts(query)
            query_hist[qa["movement"]] += 1
            signs = tuple((d < 0) - (d > 0) for d in qa["delta"])
            mode = "mono" if len(qa["colors"]) == 1 else "multi"
            query_joint[f"{signs}:{mode}"] += 1
        query_missing = sorted(set(required) - set(query_hist))
        summary = {"histograms": {k: dict(sorted(v.items())) for k,v in hist.items()},
                   "unique_supports": len(supports), "unique_inputs": len(inputs),
                   "interior_count": interior, "mirror_disagreements": mirror_errors,
                   "validation_failures": validator_errors,
                   "diagonal_only_rival_kills": rival_killed,
                   "lesson_windows_checked": max(0, count-module.EXAMPLES_NEEDED),
                   "lesson_windows_failed": windows_failed,
                   "missing_canonical_movements": missing,
                   "fixed_query_probe": {"sample_index": module.EXAMPLES_NEEDED,
                       "seeds": [0, 31], "movement_histogram": dict(sorted(query_hist.items())),
                       "direction_color_histogram": dict(sorted(query_joint.items())),
                       "missing_canonical_movements": query_missing},
                   "examples": example_by_class}
        result["bands"][band] = summary
        if missing:
            result["failures"].append({"band": band, "missing_canonical_movements": missing})
        if query_missing:
            result["failures"].append({"band": band, "query_missing_canonical_movements": query_missing})
        if mirror_errors or validator_errors or windows_failed:
            result["failures"].append({"band": band, "mirror_errors": mirror_errors,
                "validator_errors": validator_errors, "lesson_windows_failed": windows_failed})
    result["passed"] = not result["failures"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--seed", type=int, default=20260927)
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--require-support", action="store_true")
    args = parser.parse_args()
    if args.count < 8:
        parser.error("--count must be at least 8")
    source = args.generator or args.library / f"generators/{TASK_ID}/generator.py"
    module = load_generator(args.library, source)
    canonical = next(json.loads(s) for s in
                     (args.library / "shared/data/canonical/puzzles.jsonl").open()
                     if json.loads(s).get("task_id") == TASK_ID)
    result = census(module, canonical, args.seed, args.count)
    result["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    result["generator_version"] = module.VERSION
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+"\n")
    for band, row in result["bands"].items():
        print(band, {k: row[k] for k in ("unique_supports", "interior_count",
            "diagonal_only_rival_kills", "missing_canonical_movements", "lesson_windows_failed")})
    print("support gate:", "PASS" if result["passed"] else "FAIL")
    return int(args.require_support and not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
