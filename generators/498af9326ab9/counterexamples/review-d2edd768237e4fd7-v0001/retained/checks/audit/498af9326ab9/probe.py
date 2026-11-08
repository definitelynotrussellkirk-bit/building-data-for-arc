#!/usr/bin/env python3
"""Source-bound support audit for generator 498af9326ab9.

Run from the packet root via:
  python3 review.py run python3 ../checks/audit/498af9326ab9/probe.py
Then obtain the authority output with:
  python3 review.py run python3 -m arcpuzzles apply 498af9326ab9 \
    --input ../checks/audit/498af9326ab9/input.json \
    --out ../checks/audit/498af9326ab9/racket.json
Finally verify the retained Racket receipt:
  python3 review.py run python3 ../checks/audit/498af9326ab9/probe.py \
    --racket ../checks/audit/498af9326ab9/racket.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys

sys.dont_write_bytecode = True
TASK = "498af9326ab9"
EXPECTED_SOURCE_SHA256 = "f19086ed76a796847d938f1e6499dce712b233f42d9955d2758106abbbc8ff68"
REPO = Path.cwd().resolve()
HERE = REPO.parent / "checks" / "audit" / TASK
SOURCE = REPO / "generators" / TASK / "generator.py"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid) -> str:
    return sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def load_generator():
    source_sha = sha_bytes(SOURCE.read_bytes())
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"audit source changed: expected {EXPECTED_SOURCE_SHA256}, got {source_sha}")
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location("audit_498_generator", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, source_sha


def marker_positions(grid):
    start = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1)
    goal = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    return start, goal


def southeast_ordered(start, goal):
    return start[0] <= goal[0] and start[1] <= goal[1]


def swap_markers(grid):
    return [[2 if value == 1 else 1 if value == 2 else value for value in row] for row in grid]


def orientation_guarded_rival(grid, intended):
    """A brittle shortcut: solve only the blue-NW-of-red half of the domain."""
    start, goal = marker_positions(grid)
    if southeast_ordered(start, goal):
        return [row[:] for row in intended]
    return [row[:] for row in grid]


def mismatch_cells(left, right):
    return [
        [r, c]
        for r, (lrow, rrow) in enumerate(zip(left, right))
        for c, (lv, rv) in enumerate(zip(lrow, rrow))
        if lv != rv
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--racket", type=Path)
    args = parser.parse_args()
    HERE.mkdir(parents=True, exist_ok=True)
    gen, source_sha = load_generator()

    by_profile = Counter()
    relation_counts = Counter()
    accepted = 0
    exact_cases = 0
    # Exercise every declared profile in every band and a large default sample.
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for profile_index, profile in enumerate(gen.SCENE_PROFILES):
            for index in range(100):
                seed = 1_000_000 * band_index + 10_000 * profile_index + index
                grid = gen.generate(seed, index * 17, difficulty=band, scene_profile=profile)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    raise AssertionError((band, profile, index, errors))
                observed = gen.observe_overrides(grid)
                if observed != {"scene_profile": profile}:
                    raise AssertionError((profile, observed))
                start, goal = marker_positions(grid)
                relation_counts[(start[0] <= goal[0], start[1] <= goal[1])] += 1
                by_profile[profile] += 1
                accepted += 1
                exact_cases += 1

    default_unique = set()
    for index in range(5000):
        band = (None, "easy", "medium", "hard")[index % 4]
        grid = gen.generate(50_000 + index, index * 31, difficulty=band)
        errors = gen.self_check(grid, difficulty=band)
        if errors:
            raise AssertionError((index, errors))
        start, goal = marker_positions(grid)
        relation_counts[(start[0] <= goal[0], start[1] <= goal[1])] += 1
        by_profile[gen.observe_overrides(grid)["scene_profile"]] += 1
        default_unique.add(tuple(map(tuple, grid)))
        accepted += 1

    if relation_counts != {(True, True): accepted}:
        raise AssertionError(relation_counts)

    original = gen.generate(
        498_2026,
        17,
        difficulty="medium",
        scene_profile="open_rectangle",
    )
    swapped = swap_markers(original)
    original_start, original_goal = marker_positions(original)
    swapped_start, swapped_goal = marker_positions(swapped)
    assert southeast_ordered(original_start, original_goal)
    assert not southeast_ordered(swapped_start, swapped_goal)
    swapped_errors = gen.self_check(swapped, difficulty="medium")
    if swapped_errors:
        raise AssertionError(f"swapped witness unexpectedly rejected: {swapped_errors}")
    observed = gen.observe_overrides(swapped)
    if observed != {"scene_profile": "open_rectangle"}:
        raise AssertionError(observed)
    intended_original = gen.rule_mirror(original)
    intended_swapped = gen.rule_mirror(swapped)
    original_union = {(r, c) for r, row in enumerate(intended_original) for c, value in enumerate(row) if value == 8}
    swapped_union = {(r, c) for r, row in enumerate(intended_swapped) for c, value in enumerate(row) if value == 8}
    if original_union != swapped_union:
        raise AssertionError("shortest-path union should be invariant to swapping endpoint colors")
    rival = orientation_guarded_rival(swapped, intended_swapped)
    diff = mismatch_cells(intended_swapped, rival)
    if not diff:
        raise AssertionError("orientation-guarded rival did not disagree")

    input_path = HERE / "input.json"
    input_path.write_text(json.dumps({"inputs": [swapped]}, indent=2) + "\n")
    evidence = {
        "schema": "arcpuzzles-audit-support-v1",
        "task_id": TASK,
        "generator_sha256": source_sha,
        "rule_hash": gen.RULE_HASH,
        "finding": "all emitted scenes place blue weakly northwest of red, despite an accepted color-swapped open scene",
        "sample": {
            "exact_profile_band_cases": exact_cases,
            "default_cases": 5000,
            "total_accepted": accepted,
            "relation_counts": {
                f"start_row_le_goal_row={key[0]},start_col_le_goal_col={key[1]}": value
                for key, value in sorted(relation_counts.items())
            },
            "profile_counts": dict(sorted(by_profile.items())),
            "default_unique_inputs": len(default_unique),
        },
        "witness": {
            "seed": 498_2026,
            "sample_index": 17,
            "difficulty": "medium",
            "profile": "open_rectangle",
            "original_start": list(original_start),
            "original_goal": list(original_goal),
            "swapped_start": list(swapped_start),
            "swapped_goal": list(swapped_goal),
            "swapped_self_check": swapped_errors,
            "swapped_observed_axes": observed,
            "input": swapped,
            "python_mirror_output": intended_swapped,
            "orientation_guarded_rival_output": rival,
            "differing_cells": diff,
            "input_sha256": grid_sha(swapped),
            "mirror_output_sha256": grid_sha(intended_swapped),
            "rival_output_sha256": grid_sha(rival),
        },
        "commands": {
            "prepare": ["python3", "review.py", "run", "python3", "../checks/audit/498af9326ab9/probe.py"],
            "apply": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", "../checks/audit/498af9326ab9/input.json", "--out", "../checks/audit/498af9326ab9/racket.json"],
        },
    }

    if args.racket:
        receipt = json.loads(args.racket.read_text())
        results = receipt.get("results", [])
        if len(results) != 1 or results[0].get("error") is not None:
            raise AssertionError(receipt)
        racket_output = results[0]["output"]
        if racket_output != intended_swapped:
            raise AssertionError("Racket output disagrees with independent Python mirror")
        evidence["racket_verification"] = {
            "path": str(args.racket),
            "executed_rule_hash": receipt.get("executed_rule_hash"),
            "generator_sha256": receipt.get("generator_sha256"),
            "valid_output": results[0].get("valid_output"),
            "matches_python_mirror": True,
            "output_sha256": results[0].get("output_sha256"),
        }

    (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "task_id": TASK,
        "total_accepted": accepted,
        "all_blue_northwest_of_red": True,
        "swapped_witness_accepted": not swapped_errors,
        "rival_diff_cells": len(diff),
        "racket_verified": "racket_verification" in evidence,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
