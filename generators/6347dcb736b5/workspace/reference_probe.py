"""Independent geometry oracle and probes for task 6347dcb736b5.

This file deliberately does not import generator.py.  It is reusable by future
reviewers when checking generated inputs against the selected Racket authority.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Iterable

Grid = list[list[int]]


def objects(grid: Grid) -> list[dict]:
    """Return same-colour 4-connected components in row-major order."""
    if not grid or not grid[0]:
        return []
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                r, c = current
                for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _paint_bboxes(grid: Grid, *, fill: bool, keep_input: bool) -> Grid:
    output = deepcopy(grid) if keep_input else [[0] * len(grid[0]) for _ in grid]
    for obj in objects(grid):
        row1, col1, row2, col2 = obj["bbox"]
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                if fill or row in (row1, row2) or col in (col1, col2):
                    output[row][col] = obj["color"]
    return output


def oracle(grid: Grid) -> Grid:
    """Python mirror of the selected rule: bbox outlines on a fresh canvas."""
    return _paint_bboxes(grid, fill=False, keep_input=False)


def fill_bbox(grid: Grid) -> Grid:
    """Plausible rival: fill every bbox instead of outlining it."""
    return _paint_bboxes(grid, fill=True, keep_input=False)


def outline_over_input(grid: Grid) -> Grid:
    """Plausible rival: add outlines without erasing source interiors."""
    return _paint_bboxes(grid, fill=False, keep_input=True)


def global_color_bbox(grid: Grid) -> Grid:
    """Canonical-fitting rival: merge disconnected regions sharing a colour."""
    output = [[0] * len(grid[0]) for _ in grid]
    colors = sorted({value for row in grid for value in row if value})
    for color in colors:
        cells = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == color
        ]
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        row1, col1, row2, col2 = min(rows), min(cols), max(rows), max(cols)
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                if row in (row1, row2) or col in (col1, col2):
                    output[row][col] = color
    return output


def facts(grid: Grid) -> dict[str, object]:
    comps = objects(grid)
    interior_cells = 0
    hollow_boxes = 0
    for obj in comps:
        row1, col1, row2, col2 = obj["bbox"]
        if row2 - row1 + 1 >= 3 and col2 - col1 + 1 >= 3:
            hollow_boxes += 1
            interior_cells += sum(
                row1 < row < row2 and col1 < col < col2
                for row, col in obj["cells"]
            )
    return {
        "height": len(grid),
        "width": len(grid[0]) if grid else 0,
        "n_objects": len(comps),
        "colors": tuple(obj["color"] for obj in comps),
        "has_repeated_component_color": len({obj["color"] for obj in comps}) < len(comps),
        "hollow_bboxes": hollow_boxes,
        "interior_blob_cells": interior_cells,
        "occupied": sum(value != 0 for row in grid for value in row),
    }


def profile_signature(grid: Grid) -> tuple[int, int, int]:
    """(height, width, palette-size including background)."""
    colors = {value for row in grid for value in row}
    return len(grid), len(grid[0]), len(colors)
