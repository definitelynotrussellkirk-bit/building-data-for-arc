"""Executable finite rival models for the relation-matrix family.

These models are intentionally small and source-local.  They are useful for
checking whether every visible demonstration can be fit by a plausible shortcut
that later changes a query.  Passing them is finite evidence, not uniqueness.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

MODEL_NAMES = (
    "rotation",
    "dihedral",
    "translation_only",
    "direct_mirror_only",
    "area_only",
    "area_bbox",
    "color_only",
    "all_unique",
    "all_equal",
    "first_pair_only",
)

_DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("expected a nonempty grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular exact ARC integers")
    return grid


def _norm(cells):
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _turn(cells):
    return _norm((c, -r) for r, c in cells)


def _mirror(cells):
    return _norm((r, -c) for r, c in cells)


def _rotations(cells):
    current = _norm(cells)
    values = []
    for _ in range(4):
        values.append(current)
        current = _turn(current)
    return tuple(values)


def _components(grid):
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    result = []
    while remaining:
        seed = min(remaining)
        color = grid[seed[0]][seed[1]]
        remaining.remove(seed)
        queue = deque([seed])
        cells = []
        while queue:
            point = queue.popleft()
            cells.append(point)
            r, c = point
            for dr, dc in _DIR4:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        top = min(r for r, _ in cells)
        left = min(c for _, c in cells)
        bottom = max(r for r, _ in cells)
        right = max(c for _, c in cells)
        result.append({
            "color": color,
            "cells": tuple(sorted(cells)),
            "norm": _norm(cells),
            "bbox": (bottom - top + 1, right - left + 1),
        })
    return sorted(result, key=lambda obj: (
        min(r for r, _ in obj["cells"]), min(c for _, c in obj["cells"])
    ))


def _key(obj, model: str, index: int):
    cells = obj["norm"]
    if model == "rotation":
        return min(_rotations(cells))
    if model == "dihedral":
        return min((*_rotations(cells), *_rotations(_mirror(cells))))
    if model == "translation_only":
        return cells
    if model == "direct_mirror_only":
        return min(cells, _mirror(cells))
    if model == "area_only":
        return len(cells)
    if model == "area_bbox":
        return len(cells), obj["bbox"]
    if model == "color_only":
        return obj["color"]
    if model == "all_unique":
        return index
    if model == "all_equal":
        return 0
    raise ValueError(model)


def predict(grid: Any, model: str) -> list[list[int]]:
    if model not in MODEL_NAMES:
        raise ValueError(f"unknown rival model: {model}")
    objects = _components(grid)
    count = len(objects)
    if model == "first_pair_only":
        return [[5 if row == col else 8 if {row, col} == {0, 1} else 0
                 for col in range(count)] for row in range(count)]
    keys = [_key(obj, model, index) for index, obj in enumerate(objects)]
    return [[5 if row == col else 8 if keys[row] == keys[col] else 0
             for col in range(count)] for row in range(count)]
