"""Independent oracle and shortcut probe for task 4238cc89338a.

This file is reviewer tooling, not a label authority.  It computes the written
row-count/column-count construction directly from grid cells and exposes the
strongest simple canonical-fitting rival found during review: replace each blue
row count with that row's occupied span.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

TASK = "4238cc89338a"
ROOT = Path(__file__).resolve().parents[3]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / "generators" / TASK / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_record() -> dict:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK or row.get("id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} not found")


def canonical_demonstrations() -> list[dict]:
    """The public training demonstrations, excluding held-out canonical tests."""
    return list(canonical_record()["train"])


def canonical_pairs() -> list[dict]:
    row = canonical_record()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return canonical_demonstrations() + list(test)


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        component = {start}
        remaining.remove(start)
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return sorted(result, key=lambda cells: min(cells))


def _first_object(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    objects = _components(grid, color)
    if not objects:
        raise ValueError(f"missing color-{color} object")
    return objects[0]


def _bbox_profiles(
    cells: Iterable[tuple[int, int]], *, row_span: bool = False
) -> tuple[list[int], list[int]]:
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    rows: list[int] = []
    for r in range(r0, r1 + 1):
        cols = [c for rr, c in cells if rr == r]
        rows.append((max(cols) - min(cols) + 1) if row_span else len(cols))
    cols_profile = [
        sum((r, c) in cells for r in range(r0, r1 + 1))
        for c in range(c0, c1 + 1)
    ]
    return rows, cols_profile


def output(grid: list[list[int]], *, blue_row_span: bool = False) -> list[list[int]]:
    blue = _first_object(grid, 1)
    red = _first_object(grid, 2)
    blue_rows, _ = _bbox_profiles(blue, row_span=blue_row_span)
    _, red_cols = _bbox_profiles(red)
    return [
        [8 if col < blue_rows[row] and row < red_cols[col] else 0
         for col in range(len(red_cols))]
        for row in range(len(blue_rows))
    ]


def has_blue_row_gap(grid: list[list[int]]) -> bool:
    blue = _first_object(grid, 1)
    r0 = min(r for r, _ in blue)
    r1 = max(r for r, _ in blue)
    for r in range(r0, r1 + 1):
        cols = sorted(c for rr, c in blue if rr == r)
        if cols and cols[-1] - cols[0] + 1 > len(cols):
            return True
    return False


def observed(grid: list[list[int]]) -> dict:
    blue = _first_object(grid, 1)
    red = _first_object(grid, 2)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "blue_size": len(blue),
        "red_size": len(red),
        "profile_mode": "counterexample" if has_blue_row_gap(grid) else "compact",
    }


def shortcut_diff(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    intended = output(grid)
    rival = output(grid, blue_row_span=True)
    return [
        (r, c, intended[r][c], rival[r][c])
        for r in range(len(intended))
        for c in range(len(intended[0]))
        if intended[r][c] != rival[r][c]
    ]
