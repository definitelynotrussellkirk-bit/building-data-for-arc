"""Independent geometry probes for fd277c567993 review tests.

This module intentionally does not import helpers from the production generator.
It can load either the selected source or a retained baseline through
``GENERATOR_UNDER_TEST`` and reconstructs the transfer rule from pixels.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Iterable

TASK_HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or TASK_HOME / "generator.py")
    spec = importlib.util.spec_from_file_location("review_fd277c567993_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_grid(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
        and all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    )


def split_panels(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
    if not valid_grid(grid) or (len(grid[0]) - 2) % 3:
        raise ValueError("not a three-panel grid")
    panel_w = (len(grid[0]) - 2) // 3
    sep1, sep2 = panel_w, 2 * panel_w + 1
    if not all(row[sep1] == 5 and row[sep2] == 5 for row in grid):
        raise ValueError("separator columns are not color 5")
    starts = (0, sep1 + 1, sep2 + 1)
    return tuple([[*row[start:start + panel_w]] for row in grid] for start in starts)  # type: ignore[return-value]


def object_points(panel: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 8)
    }


def bbox_top(points: Iterable[tuple[int, int]]) -> tuple[int, int]:
    pts = list(points)
    if not pts:
        raise ValueError("empty object")
    return min(r for r, _ in pts), min(c for _, c in pts)


def normalize(points: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    pts = set(points)
    top, left = bbox_top(pts)
    return frozenset((r - top, c - left) for r, c in pts)


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    before, after, query = split_panels(grid)
    before_points = object_points(before)
    after_points = object_points(after)
    query_points = object_points(query)
    before_top = bbox_top(before_points)
    query_top = bbox_top(query_points)
    additions = {
        (r, c)
        for r, row in enumerate(after)
        for c, value in enumerate(row)
        if value == 8 and before[r][c] == 0
    }
    offsets = {
        (r - before_top[0], c - before_top[1])
        for r, c in additions
    }
    target_points = {
        (query_top[0] + dr, query_top[1] + dc)
        for dr, dc in offsets
        if 0 <= query_top[0] + dr < len(query)
        and 0 <= query_top[1] + dc < len(query[0])
    }
    before_colors = {before[r][c] for r, c in before_points}
    query_colors = {query[r][c] for r, c in query_points}
    return {
        "panel_h": len(before),
        "panel_w": len(before[0]),
        "shape_size_ab": len(before_points),
        "shape_size_c": len(query_points),
        "n_diff": len(additions),
        "palette_kind": "separator_shared" if before_colors == {5} else "distinct",
        "offset_relation": "overwrite" if target_points & query_points else "clear",
        "before_top": before_top,
        "query_top": query_top,
        "before_shape": normalize(before_points),
        "query_shape": normalize(query_points),
        "before_colors": before_colors,
        "query_colors": query_colors,
        "offsets": frozenset(offsets),
        "targets": frozenset(target_points),
        "query_points": frozenset(query_points),
        "after_shape": normalize(after_points),
    }


def independent_rule(grid: list[list[int]]) -> list[list[int]]:
    before, after, query = split_panels(grid)
    before_points = object_points(before)
    query_points = object_points(query)
    before_top = bbox_top(before_points)
    query_top = bbox_top(query_points)
    offsets = [
        (r - before_top[0], c - before_top[1])
        for r, row in enumerate(after)
        for c, value in enumerate(row)
        if value == 8 and before[r][c] == 0
    ]
    out = copy.deepcopy(query)
    for dr, dc in offsets:
        r, c = query_top[0] + dr, query_top[1] + dc
        if 0 <= r < len(out) and 0 <= c < len(out[0]):
            out[r][c] = 8
    return out


def canonical_pairs(task_id: str) -> list[dict[str, list[list[int]]]]:
    """Load public canonical pairs through the portable helper, with a source-tree fallback."""
    try:
        from scripts.canonical_profile_gate import canonical_pairs as shared_pairs
    except ModuleNotFoundError:
        ledger = TASK_HOME.parents[1] / "shared" / "data" / "canonical" / "puzzles.jsonl"
        pairs = []
        with ledger.open(encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("task_id") != task_id:
                    continue
                train = row.get("train") or []
                test = row.get("test") or []
                if isinstance(test, dict):
                    test = [test]
                for pair in [*train, *test]:
                    if isinstance(pair, dict) and pair.get("input") and pair.get("output"):
                        pairs.append({"input": pair["input"], "output": pair["output"]})
        return pairs
    return shared_pairs(task_id)
