#!/usr/bin/env python3
"""Independent geometry oracle and inspection helpers for task 0a1bba9e3d93.

This module intentionally does not import implementation helpers from generator.py.
It lets tests and future reviewers cross-check the selected Python sampler against
an independently transcribed version of the canonical Racket transform.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "0a1bba9e3d93"


def load_generator(path: str | Path | None = None):
    path = Path(path) if path else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_under_test", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs(path: str | Path | None = None) -> list[dict[str, Any]]:
    if path is None:
        path = Path(__file__).resolve().parents[3] / "shared/data/canonical/puzzles.jsonl"
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            test = row.get("test", [])
            if isinstance(test, dict):
                test = [test]
            rows.extend(row.get("train", []))
            rows.extend(test)
    if not rows:
        raise KeyError(f"canonical task {TASK_ID} not found in {path}")
    return rows


def split_panels(grid: list[list[int]]) -> tuple[list[list[int]], ...]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if width < 11 or (width - 2) % 3:
        raise ValueError(f"width {width} is not three panels plus two separators")
    panel_w = (width - 2) // 3
    return tuple(
        [row[index * (panel_w + 1): index * (panel_w + 1) + panel_w] for row in grid]
        for index in range(3)
    )


def cells(panel: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value != 0
    ]


def normalize(points: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = tuple(points)
    if not points:
        raise ValueError("cannot normalize an empty support")
    row0 = min(row for row, _ in points)
    col0 = min(col for _, col in points)
    return frozenset((row - row0, col - col0) for row, col in points)


def oracle(grid: list[list[int]]) -> list[list[int]]:
    """Independent transcription of the selected bbox-relative delta rule."""
    before, after, query = split_panels(grid)
    before_cells, after_cells, query_cells = cells(before), cells(after), cells(query)
    if not before_cells or not after_cells or not query_cells:
        raise ValueError("all three panels must contain foreground")
    delta = normalize(after_cells) - normalize(before_cells)
    qrow = min(row for row, _ in query_cells)
    qcol = min(col for _, col in query_cells)
    query_color = query[query_cells[0][0]][query_cells[0][1]]
    out = [row[:] for row in query]
    for drow, dcol in sorted(delta):
        row, col = qrow + drow, qcol + dcol
        if 0 <= row < len(out) and 0 <= col < len(out[0]):
            out[row][col] = query_color
    return out


def facts(grid: list[list[int]]) -> dict[str, Any]:
    before, after, query = split_panels(grid)
    bc, ac, qc = cells(before), cells(after), cells(query)
    bnorm, anorm, qnorm = normalize(bc), normalize(ac), normalize(qc)
    delta = anorm - bnorm
    qrow = min(row for row, _ in qc)
    qcol = min(col for _, col in qc)
    stamps = [(qrow + row, qcol + col) for row, col in delta]
    in_bounds = [
        point for point in stamps
        if 0 <= point[0] < len(query) and 0 <= point[1] < len(query[0])
    ]
    clipped = [point for point in stamps if point not in in_bounds]
    if clipped:
        texture = "clip"
    elif qnorm != bnorm:
        texture = "diff_query"
    else:
        texture = "plain"
    return {
        "grid_h": len(grid),
        "panel_w": len(before[0]),
        "texture": texture,
        "before_support": bnorm,
        "after_support": anorm,
        "query_support": qnorm,
        "delta": frozenset(delta),
        "in_bounds_stamps": tuple(in_bounds),
        "clipped_stamps": tuple(clipped),
    }
