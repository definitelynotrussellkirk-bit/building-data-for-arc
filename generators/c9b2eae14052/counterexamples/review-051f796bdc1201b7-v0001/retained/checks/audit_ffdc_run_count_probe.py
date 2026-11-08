#!/usr/bin/env python3
"""Adversarial probe for ffdc7818d842: count blue runs instead of blue cells."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

TASK_ID = "ffdc7818d842"
RUNTIME = Path(__file__).resolve().parent / "audit-runtime-ffdc"
sys.path.insert(0, str(RUNTIME))

from puzzle_generators import runner  # noqa: E402
from puzzle_generators.per_puzzle.ffdc7818d842 import generator as gen  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_count(positions: list[int]) -> int:
    ordered = sorted(positions)
    return sum(index == 0 or value != ordered[index - 1] + 1 for index, value in enumerate(ordered))


def rival_count_runs(grid: list[list[int]]) -> list[list[int]]:
    """Pack one cell per contiguous blue run rather than one per blue cell."""
    analysis = gen._analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed scene")
    height, width = analysis["height"], analysis["width"]
    marker_r, marker_c = analysis["marker"]
    direction = analysis["direction"]
    output = [[0 for _ in range(width)] for _ in range(height)]
    output[marker_r][marker_c] = 8

    if direction in ("left", "right"):
        for row in range(height):
            positions = [col for col in range(width) if grid[row][col] == 1]
            count = run_count(positions)
            if direction == "right":
                wall = marker_c if row == marker_r else width
                new_lo = wall - count
                for col in range(new_lo, wall):
                    output[row][col] = 1
                if row == marker_r and positions:
                    for col in range(min(positions), new_lo):
                        output[row][col] = 9
            else:
                wall = marker_c + 1 if row == marker_r else 0
                new_hi = wall + count
                for col in range(wall, new_hi):
                    output[row][col] = 1
                if row == marker_r and positions:
                    for col in range(new_hi, max(positions) + 1):
                        output[row][col] = 9
    else:
        for col in range(width):
            positions = [row for row in range(height) if grid[row][col] == 1]
            count = run_count(positions)
            if direction == "down":
                wall = marker_r if col == marker_c else height
                new_lo = wall - count
                for row in range(new_lo, wall):
                    output[row][col] = 1
                if col == marker_c and positions:
                    for row in range(min(positions), new_lo):
                        output[row][col] = 9
            else:
                wall = marker_r + 1 if col == marker_c else 0
                new_hi = wall + count
                for row in range(wall, new_hi):
                    output[row][col] = 1
                if col == marker_c and positions:
                    for row in range(new_hi, max(positions) + 1):
                        output[row][col] = 9
    return output


def all_canonical_pairs() -> list[dict]:
    pairs: list[dict] = []
    with (RUNTIME / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row.get("test", [])
            if isinstance(test, dict):
                test = [test]
            pairs.extend(row.get("train", []))
            pairs.extend(test)
    return pairs


def axis_adjacent(grid: list[list[int]]) -> bool:
    analysis = gen._analysis(grid)
    if analysis["direction"] in ("left", "right"):
        return any(
            grid[row][col] == grid[row][col + 1] == 1
            for row in range(len(grid))
            for col in range(len(grid[0]) - 1)
        )
    return any(
        grid[row][col] == grid[row + 1][col] == 1
        for row in range(len(grid) - 1)
        for col in range(len(grid[0]))
    )


def census() -> dict:
    result: dict[str, dict] = {}
    for band in ("easy", "medium", "hard"):
        pairs = 0
        fits = 0
        axis_adjacent_scenes = 0
        lessons_survived = 0
        cyclic_lessons_survived = 0
        for seed in range(100):
            demos = []
            for sample_index in range(5):
                grid = gen.generate(seed, sample_index, difficulty=band)
                official = gen.rule_mirror(grid)
                pairs += 1
                fits += int(rival_count_runs(grid) == official)
                axis_adjacent_scenes += int(axis_adjacent(grid))
                if sample_index < 4:
                    demos.append((grid, official))
            lessons_survived += int(all(rival_count_runs(grid) == output for grid, output in demos))
            for start in range(4):
                cyclic_demos = []
                for sample_index in range(start, start + 4):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    cyclic_demos.append((grid, gen.rule_mirror(grid)))
                cyclic_lessons_survived += int(
                    all(rival_count_runs(grid) == output for grid, output in cyclic_demos)
                )
        result[band] = {
            "seed_range": [0, 99],
            "production_pairs": pairs,
            "rival_fit_pairs": fits,
            "rival_refuted_pairs": pairs - fits,
            "axis_adjacent_scenes": axis_adjacent_scenes,
            "production_lessons": 100,
            "production_lessons_rival_survives_all_4_demos": lessons_survived,
            "cyclic_four_demo_windows": 400,
            "cyclic_windows_rival_survives": cyclic_lessons_survived,
        }
    return result


def main() -> int:
    canonical = all_canonical_pairs()
    canonical_fit = sum(rival_count_runs(pair["input"]) == pair["output"] for pair in canonical)

    counterexample = [
        [0, 0, 0, 1, 1],
        [0, 0, 0, 0, 1],
        [8, 0, 0, 1, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 0, 1],
    ]
    validator_findings = gen.self_check(counterexample)
    mirror_output = gen.rule_mirror(counterexample)
    rival_output = rival_count_runs(counterexample)

    bundle = runner._load_bundle(TASK_ID)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    try:
        racket_output = runner._apply_rule(bridge, fn_name, counterexample)
    finally:
        bridge.shutdown()

    runtime_generator = RUNTIME / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK_ID,
        "finding": "hard-band sampler never distinguishes blue-cell count from contiguous-run count",
        "generator_sha256": sha256(runtime_generator),
        "rule_hash": gen.RULE_HASH,
        "runtime_manifest_sha256": sha256(RUNTIME / "RUNTIME_MANIFEST.json"),
        "canonical": {
            "usable_pairs": len(canonical),
            "rival_fit_pairs": canonical_fit,
            "rival_fits_all": canonical_fit == len(canonical),
        },
        "sampler": {
            "policy": "100 seeds per band; production demos sample_index 0..3 and query 4; cyclic starts 0..3",
            "census": census(),
        },
        "counterexample": {
            "origin": "hand-constructed lawful input; not generated",
            "seed": None,
            "sample_index": None,
            "overrides": {"scene_profile": "5x5_left_mixed"},
            "input": counterexample,
            "validator_findings": validator_findings,
            "belongs_to_documented_validator_domain": validator_findings == [],
            "observed_overrides": gen.observe_overrides(counterexample),
            "actual_racket_output": racket_output,
            "python_mirror_output": mirror_output,
            "rival_output": rival_output,
            "racket_matches_mirror": racket_output == mirror_output,
            "rival_disagrees": rival_output != racket_output,
        },
        "rival": {
            "name": "pack_contiguous_blue_runs",
            "description": "replace each row/column blue-cell count with its number of contiguous blue runs, while retaining marker direction and trail logic",
        },
        "command": [
            "python3",
            "../audit_ffdc_run_count_probe.py",
        ],
        "cwd": "checks/audit-runtime-ffdc",
        "scope_note": "Finite audit of declared sampler seeds 0..99 plus all canonical rows in this packet.",
    }
    out = Path("../ffdc7818d842_run_count_shortcut.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if validator_findings == [] and racket_output == mirror_output and rival_output != racket_output else 1


if __name__ == "__main__":
    raise SystemExit(main())
