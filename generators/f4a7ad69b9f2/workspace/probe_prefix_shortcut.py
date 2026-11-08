#!/usr/bin/env python3
"""Probe bounded-prefix approximations to the crop lexicographic key.

This is review evidence, not selected generator code.  It measures a rival that
sorts by ``(width, height, crop[:N], color)`` and materializes a lawful grid on
which that rival differs from the authority.  The 9x12 construction supports
N=1 or N=2 while retaining exactly three separated monochrome objects.

Run from the packet with, for example:
    python3 run_with_racket.py python3 \
      generators/f4a7ad69b9f2/workspace/probe_prefix_shortcut.py \
      --prefix-cells 2 --out ../checks/prefix2-shortcut.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

from puzzle_generators.helpers.grid import full_grid
from reviewer_support import canonical_pairs

TASK_ID = "f4a7ad69b9f2"
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"
_spec = importlib.util.spec_from_file_location("review_target_generator", GENERATOR_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load selected generator at {GENERATOR_PATH}")
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def _shortcut_key(
    component: dict[str, object], prefix_cells: int
) -> tuple[object, ...]:
    crop = gen._crop_flat(component)
    return (
        int(component["width"]),
        int(component["height"]),
        crop[:prefix_cells],
        int(component["color"]),
    )


def prefix_then_color(
    grid: list[list[int]], prefix_cells: int
) -> list[list[int]]:
    components = sorted(
        gen._components(grid),
        key=lambda component: _shortcut_key(component, prefix_cells),
    )
    out_h = max(int(component["height"]) for component in components)
    out_w = sum(int(component["width"]) for component in components) + len(components) - 1
    output = full_grid(out_h, out_w, 0)
    left = 0
    for component in components:
        crop = gen._component_crop(component)
        for row, values in enumerate(crop):
            output[row][left : left + len(values)] = values
        left += len(crop[0]) + 1
    return output


def _prefix_shape(width: int, first_top_column: int):
    rows = []
    for row in range(3):
        if row < 2:
            rows.append("".join("1" if column == first_top_column else "0" for column in range(width)))
        else:
            rows.append("1" * width)
    return gen._shape(*rows)


def _paint(grid: list[list[int]], shape, color: int, top: int, left: int) -> None:
    for row, column in shape:
        grid[top + row][left + column] = color


def adversarial_grid(prefix_cells: int) -> list[list[int]]:
    tied_width = prefix_cells + 2
    third_width = 10 - 2 * tied_width
    if third_width < 1:
        raise ValueError("9x12 adversary supports only one- or two-cell prefixes")

    # Both tied crops share N leading zero cells.  Low-color A becomes nonzero
    # at N; high-color B remains zero until N+1.  Full lex orders B before A,
    # while the bounded-prefix rival exhausts its prefix and falls back to color.
    shape_a = _prefix_shape(tied_width, prefix_cells)
    shape_b = _prefix_shape(tied_width, prefix_cells + 1)
    shape_c = gen._shape("1" * third_width)
    grid = full_grid(9, 12, 0)
    _paint(grid, shape_a, 2, 1, 0)
    _paint(grid, shape_b, 8, 4, tied_width + 1)
    _paint(grid, shape_c, 5, 7, 2 * tied_width + 2)
    return grid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix-cells", type=int, choices=(1, 2), default=1)
    parser.add_argument("--samples-per-band", type=int, default=400)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.samples_per_band < 1:
        raise ValueError("--samples-per-band must be positive")

    canonical = canonical_pairs(TASK_ID, root=REPO_ROOT)
    canonical_fit = sum(
        prefix_then_color(pair["input"], args.prefix_cells) == pair["output"]
        for pair in canonical
    )

    disagreements = []
    profile_counts: dict[str, int] = {}
    generated_fit = 0
    for band in ("easy", "medium", "hard"):
        for index in range(args.samples_per_band):
            grid = gen.generate(700_000 + index, index, difficulty=band)
            profile = gen.observe_overrides(grid)["lesson_profile"]
            profile_counts[profile] = profile_counts.get(profile, 0) + 1
            agrees = (
                prefix_then_color(grid, args.prefix_cells) == gen.rule_mirror(grid)
            )
            generated_fit += int(agrees)
            if not agrees and len(disagreements) < 3:
                disagreements.append({"band": band, "index": index, "input": grid})

    adversary = adversarial_grid(args.prefix_cells)
    official = gen.rule_mirror(adversary)
    shortcut = prefix_then_color(adversary, args.prefix_cells)
    report = {
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "generator_version": gen.VERSION,
        "command": [sys.executable, *sys.argv],
        "cwd": os.getcwd(),
        "sample": {
            "bands": ["easy", "medium", "hard"],
            "seed_expression": "700000 + sample_index",
            "sample_indices": [0, args.samples_per_band - 1],
            "samples_per_band": args.samples_per_band,
        },
        "shortcut": (
            f"sort by (width, height, first {args.prefix_cells} crop cell(s), color)"
        ),
        "prefix_cells": args.prefix_cells,
        "canonical_fit": canonical_fit,
        "canonical_total": len(canonical),
        "generated_fit": generated_fit,
        "generated_total": 3 * args.samples_per_band,
        "profile_counts": profile_counts,
        "generated_disagreements": disagreements,
        "adversarial_self_check": gen.self_check(adversary),
        "adversarial_official": official,
        "adversarial_shortcut": shortcut,
        "adversarial_differs": shortcut != official,
        "adversarial_input": adversary,
    }
    out = args.out or Path(__file__).with_name("prefix_shortcut_report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
