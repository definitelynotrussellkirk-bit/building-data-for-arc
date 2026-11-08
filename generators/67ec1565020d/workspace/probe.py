"""Portable independent oracle and geometry observations for task 67ec1565020d.

The production authority remains the canonical Racket rule.  This module is only
for authoring tests and review evidence.  ``canonical()`` exposes labels, so do
not import it during either visible-only solve.
"""
from __future__ import annotations

from collections import deque
import importlib.util
import os
from pathlib import Path

TASK_ID = "67ec1565020d"


def load_generator():
    path = Path(os.environ.get(
        "GENERATOR_UNDER_TEST",
        Path(__file__).resolve().parents[1] / "generator.py",
    ))
    spec = importlib.util.spec_from_file_location("reviewed_aspect_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical():
    from reviewer_support import canonical_pairs, find_root

    return canonical_pairs(TASK_ID, root=find_root(__file__))


def objects(grid):
    """Return monochrome 4-connected non-background components."""
    remaining = {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    }
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        cells = []
        remaining.remove(start)
        while queue:
            row, column = queue.popleft()
            cells.append((row, column))
            for neighbor in (
                (row - 1, column),
                (row + 1, column),
                (row, column - 1),
                (row, column + 1),
            ):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        result.append((color, cells))
    return result


def dimensions(cells):
    return (
        max(row for row, _ in cells) - min(row for row, _ in cells) + 1,
        max(column for _, column in cells) - min(column for _, column in cells) + 1,
    )


def orientation(cells):
    height, width = dimensions(cells)
    return "tall" if height > width else "wide" if width > height else "square"


def output_color(cells):
    return {"wide": 2, "tall": 3, "square": 4}[orientation(cells)]


def python_oracle(grid, *, by_color=False, fill=False):
    groups = objects(grid)
    if by_color:
        merged = {}
        for color, cells in groups:
            merged.setdefault(color, []).extend(cells)
        groups = list(merged.items())

    out = [[0] * len(grid[0]) for _ in grid]
    for _, cells in groups:
        value = output_color(cells)
        if fill:
            row_min = min(row for row, _ in cells)
            row_max = max(row for row, _ in cells)
            column_min = min(column for _, column in cells)
            column_max = max(column for _, column in cells)
            cells = [
                (row, column)
                for row in range(row_min, row_max + 1)
                for column in range(column_min, column_max + 1)
            ]
        for row, column in cells:
            out[row][column] = value
    return out


def observation(grid):
    groups = objects(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(groups),
        "n_distinct_colors": len({color for color, _ in groups}),
    }


def has_nonrectangle(grid):
    for _, cells in objects(grid):
        height, width = dimensions(cells)
        if len(cells) < height * width:
            return True
    return False


def color_spans_aspects(grid):
    aspects = {}
    for color, cells in objects(grid):
        aspects.setdefault(color, set()).add(orientation(cells))
    return any(len(values) > 1 for values in aspects.values())
