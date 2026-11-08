"""Independent oracle and reusable distribution probe for task 8dac9e436a4c.

This module is test/review tooling, not label authority.  It deliberately does
not import production implementation helpers: component analysis and both
plausible rivals are reimplemented here from the public task semantics.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

TASK_ID = "8dac9e436a4c"


def load_generator(path=None):
    path = Path(path or Path(__file__).resolve().parents[1] / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _components(grid, color=6):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if value == color}
    result = []
    while remaining:
        start = min(remaining)
        stack = [start]
        remaining.remove(start)
        cells = {start}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(cells)
    return result


def analyze(grid):
    frames, solids, invalid = [], [], []
    for cells in _components(grid):
        rs = [p[0] for p in cells]
        cs = [p[1] for p in cells]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        full = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        border = {p for p in full if p[0] in (r0, r1) or p[1] in (c0, c1)}
        record = {"bbox": (r0, c0, r1, c1), "cells": cells,
                  "height": r1 - r0 + 1, "width": c1 - c0 + 1}
        if record["height"] >= 3 and record["width"] >= 3 and cells == border:
            frames.append(record)
        elif cells == full:
            solids.append(record)
        else:
            invalid.append(record)
    return {"frames": sorted(frames, key=lambda x: x["bbox"]),
            "solids": sorted(solids, key=lambda x: x["bbox"]),
            "invalid": invalid}


def intended_output(grid):
    out = deepcopy(grid)
    for record in analyze(grid)["frames"]:
        r0, c0, r1, c1 = record["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = 8
    return out


def first_frame_only_rival(grid):
    out = deepcopy(grid)
    frames = analyze(grid)["frames"]
    if frames:
        r0, c0, r1, c1 = frames[0]["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = 8
    return out


def fill_all_rectangles_rival(grid):
    """Wrong rule: fill every color-6 rectangular bbox, including solids."""
    out = deepcopy(grid)
    info = analyze(grid)
    for record in info["frames"] + info["solids"]:
        r0, c0, r1, c1 = record["bbox"]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = 8
    return out


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})
