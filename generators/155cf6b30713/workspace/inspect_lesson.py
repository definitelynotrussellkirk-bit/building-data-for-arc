#!/usr/bin/env python3
"""Inspect one generated 155cf6b30713 lesson without private ARC answers.

The report is source-bound and replayable: it records the selected generator
SHA-256, exact generation request, inferred transform/color map, mapped versus
pass-through query roles, structural diagnostics, and every declared rival's
cell disagreement with the Python authority mirror.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator
from review_diagnostics import structural_signature

TASK_ID = "155cf6b30713"


def _split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    p = len(grid)
    return [
        [list(row[start : start + p]) for row in grid]
        for start in (0, p + 1, 2 * p + 2)
    ]


def _colors(grid: list[list[int]]) -> list[int]:
    return sorted({value for row in grid for value in row if value != 0})


def _differing_cells(left: list[list[int]], right: list[list[int]]) -> int:
    if len(left) != len(right) or any(
        len(left_row) != len(right_row)
        for left_row, right_row in zip(left, right)
    ):
        return -1
    return sum(
        left_value != right_value
        for left_row, right_row in zip(left, right)
        for left_value, right_value in zip(left_row, right_row)
    )


def inspect_lesson(
    *,
    seed: int,
    sample_index: int,
    difficulty: str | None = None,
    panel_size: int | None = None,
    transform: str | None = None,
    root: str | Path | None = None,
    include_grids: bool = False,
) -> dict[str, Any]:
    """Generate one input and return a compact source-bound diagnostic report."""
    selected_root = Path(root) if root is not None else find_root(__file__)
    generator, source_path, digest = load_selected_generator(
        TASK_ID, root=selected_root
    )

    overrides: dict[str, Any] = {}
    if panel_size is not None:
        overrides["panel_size"] = panel_size
    if transform is not None:
        overrides["transform"] = transform

    grid = generator.generate(
        seed,
        sample_index,
        difficulty=difficulty,
        **overrides,
    )
    example_input, example_output, query = _split_panels(grid)
    code, mapping = generator.infer_relation(grid)
    expected = generator.rule_mirror(grid)
    query_colors = set(_colors(query))
    mapped = sorted(query_colors & set(mapping))
    unmapped = sorted(query_colors - set(mapping))

    rivals: dict[str, dict[str, Any]] = {}
    for name, rival in generator.LESSON_COMPETITORS.items():
        rival_output = rival(grid)
        differing_cells = _differing_cells(rival_output, expected)
        rivals[name] = {
            "refuted": rival_output != expected,
            "differing_cells": differing_cells,
        }
        if include_grids:
            rivals[name]["output"] = rival_output

    report: dict[str, Any] = {
        "task_id": TASK_ID,
        "generator_source": str(source_path),
        "generator_sha256": digest,
        "rule_hash": generator.RULE_HASH,
        "generator_version": generator.VERSION,
        "request": {
            "seed": seed,
            "sample_index": sample_index,
            "difficulty": difficulty,
            "overrides": overrides,
        },
        "self_check_errors": generator.self_check(grid),
        "observed_overrides": generator.observe_overrides(grid),
        "shape": [len(grid), len(grid[0])],
        "distinct_colors": sorted({value for row in grid for value in row}),
        "foreground_cells_per_panel": [
            sum(value != 0 for row in panel for value in row)
            for panel in (example_input, example_output, query)
        ],
        "inferred_relation": {
            "transform": code,
            "mapping": {str(source): target for source, target in sorted(mapping.items())},
        },
        "query_roles": {
            "colors": sorted(query_colors),
            "mapped": mapped,
            "unmapped": unmapped,
            "mixed": bool(mapped and unmapped),
        },
        "structural_signature": structural_signature(
            {"input": grid, "output": expected}
        ),
        "rivals": rivals,
    }
    if include_grids:
        report["input"] = grid
        report["authority_output"] = expected
    return report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seed", type=int)
    parser.add_argument("sample_index", type=int)
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default=None
    )
    parser.add_argument("--panel-size", type=int, choices=(4, 5, 6))
    parser.add_argument(
        "--transform", choices=("r1", "r2", "r3", "fh", "fv", "tr", "atr")
    )
    parser.add_argument(
        "--include-grids",
        action="store_true",
        help="include generated input and all authority/rival output grids",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="write JSON to this file instead of stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = inspect_lesson(
        seed=args.seed,
        sample_index=args.sample_index,
        difficulty=args.difficulty,
        panel_size=args.panel_size,
        transform=args.transform,
        include_grids=args.include_grids,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(payload, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
