#!/usr/bin/env python3
"""Source-hashed adversarial probes for the two assigned audit targets.

This is findings-only evidence.  It never edits a generator and uses pinned
seed/sample ranges so future reviewers can reproduce the exact denominators.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASKS = ("c920aa05c47e", "961add4a2688")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_generator(repo: Path, task_id: str):
    path = repo / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def nonzero_colors(grid: list[list[int]]) -> set[int]:
    return {value for row in grid for value in row if value != 0}


def frame_bbox(grid: list[list[int]]) -> tuple[int, int, int, int]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    ]
    if not cells:
        raise ValueError("grid has no color-8 frame cells")
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def pack_columns(
    grid: list[list[int]], *, sort_values: bool
) -> list[list[int]]:
    """Independent mirror plus a sort-by-color semantic rival."""
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    top, left, bottom, right = frame_bbox(grid)
    for row in range(top, bottom + 1):
        output[row][left] = 8
        output[row][right] = 8
    for col in range(left, right + 1):
        output[top][col] = 8
        output[bottom][col] = 8
    for col in range(left + 1, right):
        values = [
            grid[row][col]
            for row in range(top + 1, bottom)
            if grid[row][col] not in (0, 8)
        ]
        if sort_values:
            values = sorted(values)
        for offset, value in enumerate(values):
            output[top + 1 + offset][col] = value
    return output


def probe_c920(repo: Path, seeds: int) -> dict[str, Any]:
    generator, source = load_generator(repo, "c920aa05c47e")

    anchor_equal = []
    all_three_missing: list[dict[str, Any]] = []
    for seed in range(seeds):
        without_anchor = generator.generate(seed, 0, anchor_corner=False)
        with_anchor = generator.generate(seed, 0, anchor_corner=True)
        if without_anchor == with_anchor:
            anchor_equal.append(seed)

        grid = generator.generate(
            seed,
            0,
            n_cells=3,
            color_distribution="all_three",
            position_bias="scattered",
        )
        colors = sorted(nonzero_colors(grid))
        if colors != [2, 3, 8]:
            all_three_missing.append({"seed": seed, "observed_colors": colors})

    return {
        "task_id": "c920aa05c47e",
        "generator_sha256": sha256(source),
        "seed_range": [0, seeds - 1],
        "anchor_corner": {
            "identical_true_false_pairs": len(anchor_equal),
            "draws": seeds,
            "first_equal_seeds": anchor_equal[:10],
            "interpretation": "declared boolean override is observationally inert",
        },
        "all_three": {
            "missing_one_or_more_colors": len(all_three_missing),
            "draws": seeds,
            "first_counterexamples": all_three_missing[:10],
            "interpretation": "the all_three label does not guarantee all three source colors",
        },
    }


def probe_961(repo: Path, seeds: int, lessons: int) -> dict[str, Any]:
    generator, source = load_generator(repo, "961add4a2688")
    axis_values = {
        "palette_kind": tuple(generator.PALETTE_KINDS),
        "texture": tuple(generator.PALETTE_KINDS),
        "palette_size": (2, 8),
        "n_distinct_colors": (2, 8),
    }
    dead_axes: dict[str, Any] = {}
    for axis, values in axis_values.items():
        equal_seeds = []
        for seed in range(seeds):
            grids = [generator.generate(seed, 0, **{axis: value}) for value in values]
            if all(grid == grids[0] for grid in grids[1:]):
                equal_seeds.append(seed)
        dead_axes[axis] = {
            "values": list(values),
            "identical_across_values": len(equal_seeds),
            "draws": seeds,
            "first_equal_seeds": equal_seeds[:10],
        }

    two_marker_generation_rejections = []
    two_marker_self_check_rejections = []
    for seed in range(seeds):
        try:
            grid = generator.generate(seed, 0, n_markers=2)
        except Exception as exc:  # the contradiction itself is audit evidence
            two_marker_generation_rejections.append(
                {"seed": seed, "exception": type(exc).__name__, "message": str(exc)}
            )
            continue
        errors = generator.self_check(grid)
        if errors:
            two_marker_self_check_rejections.append({"seed": seed, "errors": errors})

    rival_by_band: dict[str, Any] = {}
    for difficulty in ("easy", "medium", "hard"):
        surviving_lessons = []
        matching_rows = 0
        for seed in range(lessons):
            grids = [
                generator.generate(seed, sample_index, difficulty=difficulty)
                for sample_index in range(4)
            ]
            matches = [
                pack_columns(grid, sort_values=False)
                == pack_columns(grid, sort_values=True)
                for grid in grids
            ]
            matching_rows += sum(matches)
            if all(matches):
                surviving_lessons.append(seed)
        rival_by_band[difficulty] = {
            "sort_by_color_rival_surviving_lessons": len(surviving_lessons),
            "lessons": lessons,
            "matching_rows": matching_rows,
            "rows": lessons * 4,
            "first_surviving_seeds": surviving_lessons[:10],
        }

    return {
        "task_id": "961add4a2688",
        "generator_sha256": sha256(source),
        "axis_seed_range": [0, seeds - 1],
        "dead_axis_pairs": dead_axes,
        "n_markers_two": {
            "generation_rejections": len(two_marker_generation_rejections),
            "self_check_rejections": len(two_marker_self_check_rejections),
            "draws": seeds,
            "first_generation_rejections": two_marker_generation_rejections[:5],
            "first_self_check_rejections": two_marker_self_check_rejections[:5],
            "interpretation": (
                "AXES advertises 2 as valid, but the ordinary generator range "
                "rejects it before construction; self_check separately requires at least 3"
            ),
        },
        "order_preservation_shortcut": {
            "lesson_seed_range": [0, lessons - 1],
            "examples_per_lesson": 4,
            "rival": "pack each column upward after sorting its colors numerically",
            "bands": rival_by_band,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--axis-seeds", type=int, default=200)
    parser.add_argument("--lessons", type=int, default=200)
    parser.add_argument("--json-out", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo.resolve()
    payload = {
        "schema": "arcpuzzles-findings-only-audit-probe-v1",
        "parameters": {
            "axis_seed_range": [0, args.axis_seeds - 1],
            "lesson_seed_range": [0, args.lessons - 1],
            "examples_per_lesson": 4,
        },
        "audits": [
            probe_c920(repo, args.axis_seeds),
            probe_961(repo, args.axis_seeds, args.lessons),
        ],
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
