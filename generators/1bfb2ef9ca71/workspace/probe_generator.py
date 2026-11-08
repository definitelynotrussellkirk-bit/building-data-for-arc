#!/usr/bin/env python3
"""Source-bound structural and teaching probe for generator 1bfb2ef9ca71.

Run through the packet wrapper so ``reviewer_support`` and the selected runtime
are available.  The Python mirror is diagnostic only; canonical Racket remains
label authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "1bfb2ef9ca71"
BANDS = ("easy", "medium", "hard")


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _pair(gen: Any, grid: list[list[int]]) -> dict[str, Any]:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def run(*, seeds: int, indices: int) -> dict[str, Any]:
    root = find_root(__file__)
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    failures: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    unique_inputs: set[str] = set()

    for band in BANDS:
        for seed in range(seeds):
            for sample_index in range(indices):
                try:
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    replay = gen.generate(seed, sample_index, difficulty=band)
                    analysis = gen._analyze(grid)
                    errors = gen.self_check(grid, difficulty=band)
                    if replay != grid:
                        failures.append({
                            "kind": "nondeterministic",
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                        })
                    if errors:
                        failures.append({
                            "kind": "self_check",
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        })
                    unique_inputs.add(_grid_hash(grid))
                    counts[f"band:{band}"] += 1
                    counts[f"shape:{len(grid)}x{len(grid[0])}"] += 1
                    counts[f"rectangles:{len(analysis['boxes'])}"] += 1
                    counts[f"schedule:{gen.schedule_profile(seed, sample_index, band)}"] += 1
                    counts[f"witness:non_three_height:{gen.SEMANTIC_WITNESSES['non_three_height'](grid)}"] += 1
                    counts[f"both_orientations:{set(analysis['orientations']) == {'nw_se', 'ne_sw'}}"] += 1
                except Exception as exc:  # retain exact failing coordinates
                    failures.append({
                        "kind": "exception",
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": repr(exc),
                    })

    exact_axis_checks: list[dict[str, Any]] = []
    for band in BANDS:
        for height in range(8, 13):
            for width in range(7, 15):
                for rectangles in (2, 3):
                    requested = {
                        "grid_h": height,
                        "grid_w": width,
                        "rectangles": rectangles,
                    }
                    grid = gen.generate(
                        1129,
                        11,
                        difficulty=band,
                        **requested,
                    )
                    observed = gen.observe_overrides(grid)
                    errors = gen.self_check(
                        grid,
                        difficulty=band,
                        meta={"overrides": requested},
                    )
                    row = {
                        "band": band,
                        "requested": requested,
                        "observed": observed,
                        "errors": errors,
                    }
                    exact_axis_checks.append(row)
                    if observed != requested or errors:
                        failures.append({"kind": "exact_axis", **row})

    canonical_records: list[dict[str, Any]] = []
    rival = gen.CANONICAL_SHORTCUTS["fixed_height_three"]
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        record = {
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "self_check": gen.self_check(pair["input"]),
            "mirror_exact": gen.rule_mirror(pair["input"]) == pair["output"],
            "fixed_height_three_fits": rival(pair["input"]) == pair["output"],
        }
        canonical_records.append(record)
        if record["self_check"] or not record["mirror_exact"] or not record["fixed_height_three_fits"]:
            failures.append({"kind": "canonical", **record})

    rotation_checks: list[dict[str, Any]] = []
    for band in BANDS:
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            bundle = [
                _pair(gen, gen.generate(731, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            for query_position in range(len(bundle)):
                query = bundle[query_position]
                demos = [pair for pos, pair in enumerate(bundle) if pos != query_position]
                reasons = gen.lesson_identifiable(demos, query)
                surviving = [
                    name
                    for name, competitor in gen.LESSON_COMPETITORS.items()
                    if all(competitor(pair["input"]) == pair["output"] for pair in demos)
                ]
                row = {
                    "band": band,
                    "start_residue": start,
                    "query_position": query_position,
                    "identifiability_reasons": reasons,
                    "surviving_rivals": surviving,
                    "non_three_demo_count": sum(
                        gen.SEMANTIC_WITNESSES["non_three_height"](pair["input"])
                        for pair in demos
                    ),
                }
                rotation_checks.append(row)
                if reasons or surviving or row["non_three_demo_count"] < 1:
                    failures.append({"kind": "rotation", **row})

    return {
        "schema": "arc-generator-1bfb2ef9ca71-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(source),
        "generator_sha256": source_sha256,
        "settings": {
            "bands": list(BANDS),
            "seeds": seeds,
            "indices_per_seed_band": indices,
            "schedule_seed": 731,
        },
        "generated": {
            "draws": len(BANDS) * seeds * indices,
            "unique_inputs": len(unique_inputs),
            "counts": dict(sorted(counts.items())),
        },
        "exact_axes": {
            "checks": len(exact_axis_checks),
            "all_exact": all(
                row["requested"] == row["observed"] and not row["errors"]
                for row in exact_axis_checks
            ),
        },
        "canonical": {
            "pairs": len(canonical_records),
            "records": canonical_records,
        },
        "schedule": {
            "demonstrations": gen.EXAMPLES_NEEDED,
            "queries": 1,
            "declared_period": gen.LESSON_SCHEDULE_PERIOD,
            "query_policy": "all four rotations of each consecutive 3-demo + 1-query bundle",
            "checks": len(rotation_checks),
            "all_rotations_refute_declared_rivals": all(
                not row["identifiability_reasons"]
                and not row["surviving_rivals"]
                and row["non_three_demo_count"] >= 1
                for row in rotation_checks
            ),
            "records": rotation_checks,
        },
        "failures": failures,
        "status": "pass" if not failures else "fail",
        "limits": [
            "Python mirror checks are diagnostic and do not replace Racket authority.",
            "Finite seeds do not exhaust geometry support or undeclared rivals.",
            "Schedule enumeration exhausts declared start residues only at seed 731.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--indices", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds <= 0 or args.indices <= 0:
        parser.error("--seeds and --indices must be positive")
    report = run(seeds=args.seeds, indices=args.indices)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
