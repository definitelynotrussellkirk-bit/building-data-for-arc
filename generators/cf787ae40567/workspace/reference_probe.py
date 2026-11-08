"""Independent test oracle and small audit helpers for task cf787ae40567.

The selected Racket rule remains label authority.  This module deliberately
recomputes plus-stencil geometry without importing production helpers, so task
regressions can catch a generator-side mirror that drifts with the source.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterable, Sequence

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "cf787ae40567"
PROFILE_NAMES = ("canonical", "overlap", "edge", "mixed")
PLUS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path=None):
    root = find_root(__file__)
    source = Path(path or root / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_cf787ae40567", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=find_root(__file__))


def seeds(grid: Sequence[Sequence[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, int(value))
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if int(value) != 0
    ]


def plus_cells(grid: Sequence[Sequence[int]], point: tuple[int, int]) -> set[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    r, c = point
    return {
        (r + dr, c + dc)
        for dr, dc in PLUS
        if 0 <= r + dr < h and 0 <= c + dc < w
    }


def union_cells(grid: Sequence[Sequence[int]]) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for r, c, _ in seeds(grid):
        result.update(plus_cells(grid, (r, c)))
    return result


def intended_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [[8] * len(union_cells(grid))]


def five_per_seed_rival(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [[8] * (5 * len(seeds(grid)))]


def clipped_sum_without_union_rival(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    width = sum(len(plus_cells(grid, (r, c))) for r, c, _ in seeds(grid))
    return [[8] * width]


def overlap_pairs(grid: Sequence[Sequence[int]]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    points = [(r, c) for r, c, _ in seeds(grid)]
    result = []
    for i, first in enumerate(points):
        first_mask = plus_cells(grid, first)
        for second in points[i + 1 :]:
            if first_mask & plus_cells(grid, second):
                result.append((first, second))
    return result


def edge_seed_count(grid: Sequence[Sequence[int]]) -> int:
    h, w = len(grid), len(grid[0])
    return sum(r in (0, h - 1) or c in (0, w - 1) for r, c, _ in seeds(grid))


def profile_signature(grid: Sequence[Sequence[int]]) -> dict[str, object]:
    values = [value for _, _, value in seeds(grid)]
    return {
        "shape": (len(grid), len(grid[0])),
        "seed_count": len(values),
        "seed_colors": tuple(sorted(values)),
        "distinct_seed_colors": len(set(values)),
        "edge_seed_count": edge_seed_count(grid),
        "overlap_pair_count": len(overlap_pairs(grid)),
        "union_size": len(union_cells(grid)),
        "clipped_sum": sum(
            len(plus_cells(grid, (r, c))) for r, c, _ in seeds(grid)
        ),
    }


def pair(grid: Sequence[Sequence[int]]) -> dict[str, list[list[int]]]:
    materialized = [list(row) for row in grid]
    return {"input": materialized, "output": intended_output(materialized)}


def canonical_shortcuts_fit() -> dict[str, bool]:
    pairs = canonical_pairs()
    rivals = {
        "five_per_seed": five_per_seed_rival,
        "clipped_sum_without_union": clipped_sum_without_union_rival,
    }
    return {
        name: all(rival(item["input"]) == item["output"] for item in pairs)
        for name, rival in rivals.items()
    }
