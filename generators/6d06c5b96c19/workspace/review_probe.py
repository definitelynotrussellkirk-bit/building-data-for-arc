#!/usr/bin/env python3
"""Reproduce the review's shortcut, schedule, and scalar-validation probes."""
from __future__ import annotations

import argparse
from collections import Counter, deque
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "6d06c5b96c19"


def _payload(grid: list[list[int]]) -> list[list[int]]:
    return [row[1:] for row in grid]


def _cyclic_row_period(rows: list[list[int]]) -> int:
    frozen = [tuple(row) for row in rows]
    for shift in range(1, len(rows) + 1):
        if all(
            frozen[index] == frozen[(index + shift) % len(rows)]
            for index in range(len(rows))
        ):
            return shift
    raise AssertionError("finite row sequence must have a period")


def _singleton_count(grid: list[list[int]]) -> int:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    sizes: list[int] = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        remaining.remove(start)
        size = 0
        while queue:
            row, col = queue.popleft()
            size += 1
            for point in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    queue.append(point)
        sizes.append(size)
    return Counter(sizes)[1]


def run_probe() -> tuple[dict[str, Any], dict[str, Any]]:
    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root)
    shortcut = generator.CANONICAL_SHORTCUTS["four_row_instruction_code"]

    schedule: dict[str, Any] = {}
    for difficulty in ("easy", "medium", "hard"):
        grids = [generator.generate(77, index, difficulty=difficulty) for index in range(8)]
        schedule[difficulty] = {
            "duplicate_phases": [
                index
                for index, grid in enumerate(grids)
                if len({tuple(row) for row in _payload(grid)}) < len(grid)
            ],
            "periods": [_cyclic_row_period(_payload(grid)) for grid in grids],
            "marker_rows": [
                generator.observe_overrides(grid)["red_row_index"] for grid in grids
            ],
        }

    lesson_failures: list[dict[str, Any]] = []
    lesson_count = 0
    for difficulty in ("easy", "medium", "hard"):
        for start in range(24):
            demos = []
            for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
                grid = generator.generate(404, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": generator.rule_mirror(grid)})
            query_grid = generator.generate(
                404,
                start + generator.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            errors = generator.lesson_identifiable(
                demos,
                {"input": query_grid, "output": generator.rule_mirror(query_grid)},
            )
            lesson_count += 1
            if errors:
                lesson_failures.append(
                    {"difficulty": difficulty, "start": start, "errors": errors}
                )

    rejected_cases: list[str] = []
    invalid_calls = [
        ("seed_bool", (True, 0), {}),
        ("seed_float", (1.0, 0), {}),
        ("seed_string", ("1", 0), {}),
        ("index_bool", (1, True), {}),
        ("index_float", (1, 1.0), {}),
        ("index_string", (1, "1"), {}),
        ("index_negative", (1, -1), {}),
    ]
    for name, args, overrides in invalid_calls:
        try:
            generator.generate(*args, difficulty="easy", **overrides)
        except (TypeError, ValueError):
            rejected_cases.append(name)
    for axis, control in {
        "grid_h": 5,
        "grid_w": 6,
        "red_row_index": 0,
        "payload_palette_size": 3,
    }.items():
        for tag, value in (
            ("bool", True),
            ("float", float(control)),
            ("string", str(control)),
        ):
            name = f"{axis}_{tag}"
            try:
                generator.generate(1, 0, difficulty="easy", **{axis: value})
            except (TypeError, ValueError):
                rejected_cases.append(name)

    edge_singletons = []
    for seed in range(1, 9):
        for sample_index in (0, 6):
            grid = generator.generate(seed, sample_index, difficulty="medium")
            edge_singletons.append(
                {
                    "seed": seed,
                    "sample_index": sample_index,
                    "singleton_count": _singleton_count(grid),
                }
            )

    seed, sample_index, difficulty = 707, 6, "hard"
    grid = generator.generate(seed, sample_index, difficulty=difficulty)
    intended = generator.rule_mirror(grid)
    shortcut_output = shortcut(grid)
    counterexample = {
        "schema": "6d06c5b96c19-shortcut-counterexample-v1",
        "generator_sha256": source_sha256,
        "sampling": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
        },
        "shortcut": "four_row_instruction_code",
        "shortcut_definition": (
            "remove column 0 and rotate payload rows down by "
            "(red_row_index mod 4)"
        ),
        "input": grid,
        "red_row_index": generator.observe_overrides(grid)["red_row_index"],
        "intended_output": intended,
        "shortcut_output": shortcut_output,
        "disagrees": shortcut_output != intended,
        "generator_emits": True,
        "check": (
            "Python rule_mirror and executable CANONICAL_SHORTCUTS function; "
            "canonical fit checked on every canonical pair."
        ),
    }

    report = {
        "schema": "6d06c5b96c19-review-probes-v1",
        "task_id": TASK_ID,
        "version": generator.VERSION,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "canonical_shortcut": {
            "name": "four_row_instruction_code",
            "canonical_pairs": len(canonical),
            "fit_results": [
                shortcut(pair["input"]) == pair["output"] for pair in canonical
            ],
        },
        "schedule": schedule,
        "consecutive_lesson_probe": {
            "examples_per_lesson": generator.EXAMPLES_NEEDED,
            "windows_checked": lesson_count,
            "failures": lesson_failures,
            "passed": not lesson_failures,
        },
        "strict_scalar_probe": {
            "rejected_count": len(rejected_cases),
            "rejected_cases": rejected_cases,
        },
        "edge_profile_singletons": {
            "cases": edge_singletons,
            "all_exactly_one": all(
                row["singleton_count"] == 1 for row in edge_singletons
            ),
        },
        "counterexample_disagrees": counterexample["disagrees"],
    }
    return report, counterexample


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--counterexample-out", type=Path, required=True)
    args = parser.parse_args()
    report, counterexample = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.counterexample_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.counterexample_out.write_text(
        json.dumps(counterexample, indent=2, sort_keys=True) + "\n"
    )
    print(
        json.dumps(
            {
                "status": "passed" if report["consecutive_lesson_probe"]["passed"] else "failed",
                "generator_sha256": report["generator_sha256"],
                "lesson_windows": report["consecutive_lesson_probe"]["windows_checked"],
                "lesson_failures": len(report["consecutive_lesson_probe"]["failures"]),
                "strict_rejections": report["strict_scalar_probe"]["rejected_count"],
                "out": str(args.out),
                "counterexample_out": str(args.counterexample_out),
            },
            sort_keys=True,
        )
    )
    return 0 if report["consecutive_lesson_probe"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
