#!/usr/bin/env python3
"""Source-bound coverage probe for equally stacked binary-occupancy tasks.

Reports INPUT truth-table coverage, not reference-output correctness. Use the
public lesson-census/apply commands for Racket labels and lesson rival scoring.
The task ID, seed count, sample count, bands and required states are configurable.
Run through review.py run so dependencies come from this packet's own runtime.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator


def occupancy(grid):
    if not grid or len(grid) % 2 or not grid[0]:
        raise ValueError("expected two equally sized stacked panels")
    width, half = len(grid[0]), len(grid) // 2
    if any(len(row) != width for row in grid):
        raise ValueError("ragged input")
    return Counter(f"{int(top != 0)}{int(bottom != 0)}"
                   for upper, lower in zip(grid[:half], grid[half:])
                   for top, bottom in zip(upper, lower))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", default="af0ae766e671")
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--band", action="append", choices=("easy", "medium", "hard", "default"))
    parser.add_argument("--require-states", default="00,01,10,11")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.seed_count < 1 or args.samples < 1:
        parser.error("seed-count and samples must be positive")
    required = set(args.require_states.split(","))
    if not required <= {"00", "01", "10", "11"}:
        parser.error("require-states must list binary pairs separated by commas")
    if args.out.exists():
        parser.error("output already exists; choose a new evidence path")
    root = find_root(__file__)
    module, source, source_hash = load_selected_generator(args.task_id, root=root)
    pairs = canonical_pairs(args.task_id, root=root, labeled_only=True)
    canonical = [{"variant": p.get("variant"), "split": p.get("split"),
                  "pair_index": p.get("pair_index"),
                  "input_shape": [len(p["input"]), len(p["input"][0])],
                  "occupancy_counts": dict(occupancy(p["input"]))}
                 for p in pairs]
    patterns = tuple(getattr(module, "PANEL_PATTERNS", ())) or (None,)
    groups, all_hashes = [], set()
    for band in args.band or ("easy", "medium", "hard"):
        for pattern in patterns:
            counts, state_totals, shape_counts, hashes = Counter(), Counter(), Counter(), set()
            first_failure = None
            for seed in range(args.seed_count):
                for index in range(args.samples):
                    controls = {} if pattern is None else {"panel_pattern": pattern}
                    call = {"seed": seed, "sample_index": index,
                            "difficulty": None if band == "default" else band,
                            "overrides": controls}
                    counts["requested"] += 1
                    try:
                        grid = module.generate(seed, index, difficulty=call["difficulty"], **controls)
                        states = occupancy(grid)
                        issues = module.self_check(grid, difficulty=call["difficulty"])
                        digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
                        hashes.add(digest)
                        all_hashes.add(digest)
                        counts["generated"] += 1
                        state_totals.update(states)
                        shape_counts[f"{len(grid)}x{len(grid[0])}"] += 1
                        missing = sorted(required - states.keys())
                        counts["complete_state_support"] += not missing
                        counts["self_check_passed"] += not issues
                        if (missing or issues) and first_failure is None:
                            first_failure = {"call": call, "input": grid, "input_sha256": digest,
                                             "missing_states": missing, "self_check": issues}
                    except Exception as exc:
                        counts["exceptions"] += 1
                        if first_failure is None:
                            first_failure = {"call": call, "error": f"{type(exc).__name__}: {exc}"}
            groups.append({"band": band, "pattern": pattern, "counts": dict(counts),
                           "unique_inputs": len(hashes), "state_totals": dict(state_totals),
                           "shape_counts": dict(sorted(shape_counts.items())),
                           "first_failure": first_failure})
    passed = all(g["counts"].get("complete_state_support", 0) == g["counts"]["requested"]
                 and g["counts"].get("self_check_passed", 0) == g["counts"]["requested"] for g in groups)
    report = {"schema": "stacked-occupancy-coverage-v1", "task_id": args.task_id,
              "generator_sha256": source_hash, "generator_path": source.relative_to(root).as_posix(),
              "declared_rule_hash": getattr(module, "RULE_HASH", None),
              "scope": "Input coverage only; not reference labeling, production lesson assembly, or training admission.",
              "seed_range": [0, args.seed_count-1], "sample_index_range": [0, args.samples-1],
              "required_states": sorted(required), "canonical": canonical, "groups": groups,
              "requested_inputs": sum(g["counts"]["requested"] for g in groups),
              "unique_inputs": len(all_hashes), "passed": passed,
              "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd())}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in
                      ("task_id", "generator_sha256", "requested_inputs", "unique_inputs", "passed")}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
