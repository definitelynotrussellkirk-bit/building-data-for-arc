"""Independent structural oracle and reusable audit helpers for ee6a99e8b7f9.

The Python oracle is supplementary test tooling. Canonical Racket remains the
label authority; this module intentionally does not import production helpers.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

TASK = "ee6a99e8b7f9"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs as _canonical_pairs, find_root

CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def load_generator(path=None):
    path = Path(path or os.environ.get("GENERATOR_UNDER_TEST") or HOME / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_ee6a99e8b7f9", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    root = find_root(__file__)
    pairs = _canonical_pairs(TASK, root=root)
    seen = set()
    unique = []
    for pair in pairs:
        key = repr((pair["input"], pair["output"]))
        if key not in seen:
            seen.add(key)
            unique.append(pair)
    return unique


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be nonempty")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("rows must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be literal ARC colors")
    return len(grid), width


def shapes(grid):
    """Return same-color 4-connected rectangles, independently parsed."""
    h, w = _validate_grid(grid)
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] in (5, 6)}
    result = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in CARDINAL:
                p = (r + dr, c + dc)
                if p in unseen and grid[p[0]][p[1]] == color:
                    unseen.remove(p)
                    queue.append(p)
                    cells.add(p)
        r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
        c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
        result.append({"color": color, "bbox": (r1, c1, r2, c2), "cells": frozenset(cells),
                       "filled": len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1)})
    return sorted(result, key=lambda item: item["bbox"])


def association(dot, shape):
    r, c = dot
    r1, c1, r2, c2 = shape["bbox"]
    in_rows = r1 <= r <= r2
    in_cols = c1 <= c <= c2
    if in_rows and c == c1 - 1:
        return "left"
    if in_rows and c == c2 + 1:
        return "right"
    if in_cols and r == r1 - 1:
        return "above"
    if in_cols and r == r2 + 1:
        return "below"
    return None


def associations(grid):
    parsed = shapes(grid)
    dots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    result = []
    for dot in dots:
        hits = [(i, association(dot, shape)) for i, shape in enumerate(parsed)]
        hits = [(i, side) for i, side in hits if side]
        result.append((dot, hits))
    return parsed, result


def target_for(dot, shape, side, *, fixed_steps=False):
    r, c = dot
    r1, c1, r2, c2 = shape["bbox"]
    if fixed_steps:
        step = 2 if shape["color"] == 6 else 1
        delta = {"left": (0, step), "right": (0, -step),
                 "above": (step, 0), "below": (-step, 0)}[side]
        return r + delta[0], c + delta[1]
    if shape["color"] == 6:
        return (r, (c1 + c2) // 2) if side in ("left", "right") else ((r1 + r2) // 2, c)
    return {"left": (r, c1), "right": (r, c2),
            "above": (r1, c), "below": (r2, c)}[side]


def geometry_output(grid, *, fixed_steps=False, first_dot_only=False,
                    pink_inner=False, gray_center=False,
                    keep_pink_source=False, clear_gray_source=False):
    """Independent interpretation of the task and named plausible variants."""
    parsed, linked = associations(grid)
    out = deepcopy(grid)
    for shape in parsed:
        if shape["color"] == 5:
            for r, c in shape["cells"]:
                out[r][c] = 8
    seen_shapes = set()
    for dot, hits in linked:
        if len(hits) != 1:
            continue
        index, side = hits[0]
        shape = parsed[index]
        if first_dot_only and index in seen_shapes:
            continue
        seen_shapes.add(index)
        r, c = dot
        if shape["color"] == 6:
            if not keep_pink_source:
                out[r][c] = 8
            if pink_inner:
                nr, nc = target_for(dot, {**shape, "color": 5}, side)
            else:
                nr, nc = target_for(dot, shape, side, fixed_steps=fixed_steps)
        else:
            if clear_gray_source:
                out[r][c] = 8
            if gray_center:
                nr, nc = target_for(dot, {**shape, "color": 6}, side)
            else:
                nr, nc = target_for(dot, shape, side, fixed_steps=fixed_steps)
        if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
            out[nr][nc] = 9
    return out


def observed(grid):
    parsed, linked = associations(grid)
    counts = [0] * len(parsed)
    for _, hits in linked:
        if len(hits) == 1:
            counts[hits[0][0]] += 1
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_shapes": len(parsed),
        "shape_sizes": sorted((s["bbox"][2] - s["bbox"][0] + 1,
                               s["bbox"][3] - s["bbox"][1] + 1) for s in parsed),
        "colors": sorted({s["color"] for s in parsed}),
        "dot_counts": counts,
        "border_shapes": sum(any(v in (0, len(grid) - 1) for v in (s["bbox"][0], s["bbox"][2])) or
                             any(v in (0, len(grid[0]) - 1) for v in (s["bbox"][1], s["bbox"][3]))
                             for s in parsed),
    }
