"""Independent review helpers for 9686a12edc93.

This module deliberately does not import implementation helpers from generator.py.
It gives future reviewers a small oracle/analyzer for exact counterexamples and
Racket parity checks while the selected Racket program remains label authority.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Any

TASK_ID = "9686a12edc93"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def segment(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    (r1, c1), (r2, c2) = a, b
    if r1 == r2:
        lo, hi = sorted((c1, c2))
        return tuple((r1, c) for c in range(lo, hi + 1))
    if c1 == c2:
        lo, hi = sorted((r1, r2))
        return tuple((r, c1) for r in range(lo, hi + 1))
    return ()


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    errors = grid_errors(grid)
    if errors:
        return {"errors": errors, "by_color": {}, "clear": [], "blocked": [], "unaligned": []}

    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color[value].append((r, c))

    clear: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    unaligned: list[dict[str, Any]] = []
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            continue
        path = segment(cells[0], cells[1])
        record = {"color": color, "cells": tuple(cells), "path": path}
        if not path:
            unaligned.append(record)
            continue
        blockers = tuple(point for point in path[1:-1] if grid[point[0]][point[1]] != 0)
        record["blockers"] = blockers
        (blocked if blockers else clear).append(record)

    return {
        "errors": errors,
        "by_color": dict(by_color),
        "clear": clear,
        "blocked": blocked,
        "unaligned": unaligned,
    }


def colors_in_reading_order(grid: list[list[int]]) -> list[int]:
    result: list[int] = []
    for row in grid:
        for value in row:
            if value and value not in result:
                result.append(value)
    return result


def intended_output(grid: list[list[int]], *, ignore_blockers: bool = False) -> list[list[int]]:
    """Independent mirror of the selected rule; starts from an empty output."""
    if grid_errors(grid):
        raise ValueError("malformed grid")
    out = [[0 for _ in row] for row in grid]
    for color in colors_in_reading_order(grid):
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if len(cells) != 2:
            continue
        path = segment(cells[0], cells[1])
        if not path:
            continue
        if ignore_blockers or all(grid[r][c] == 0 for r, c in path[1:-1]):
            for r, c in path:
                out[r][c] = color
    return out


def copy_then_connect(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: retain invalid motifs instead of clearing them."""
    out = deepcopy(grid)
    canonical = intended_output(grid)
    for r, row in enumerate(canonical):
        for c, value in enumerate(row):
            if value:
                out[r][c] = value
    return out


def differing_cells(left: list[list[int]], right: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(len(left))
        for c in range(len(left[0]))
        if left[r][c] != right[r][c]
    ]
