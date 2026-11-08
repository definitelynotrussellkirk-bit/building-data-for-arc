"""Independent Python oracle for task ``2602c3d31d21``.

The input contains one right-edge singleton key per color and one disconnected
multi-cell body of that color.  Bodies are ordered by the key cells.  Their
pairwise-distance signatures determine the comparison matrix.
"""
from __future__ import annotations

from collections import deque
from typing import Any


METRICS = ("squared_euclidean", "manhattan")


def validate_metric(metric: Any) -> str:
    if type(metric) is not str or metric not in METRICS:
        raise ValueError(f"declared metric must be one of {METRICS}, got {metric!r}")
    return metric


def validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must lie in 1..30")
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and contain list rows")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be literal ARC integers 0..9")
    return height, width


def _components(
    grid: list[list[int]], color: int, *, body_only: bool
) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    col_stop = width - 1 if body_only else width
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(col_stop):
            if grid[row][col] != color or (row, col) in seen:
                continue
            component: list[tuple[int, int]] = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                current = queue.popleft()
                component.append(current)
                cr, cc = current
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < col_stop
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(sorted(component))
    return result


def pairwise_signature(cells: Any, metric: Any) -> int:
    selected = validate_metric(metric)
    if type(cells) not in (list, tuple) or len(cells) < 2:
        raise ValueError("a shape must contain at least two cells")
    normalized: list[tuple[int, int]] = []
    for cell in cells:
        if (
            type(cell) not in (list, tuple)
            or len(cell) != 2
            or type(cell[0]) is not int
            or type(cell[1]) is not int
        ):
            raise ValueError("shape cells must be integer coordinate pairs")
        normalized.append((cell[0], cell[1]))
    total = 0
    for index, (row1, col1) in enumerate(normalized):
        for row2, col2 in normalized[index + 1 :]:
            dr, dc = row1 - row2, col1 - col2
            if selected == "squared_euclidean":
                total += dr * dr + dc * dc
            else:
                total += abs(dr) + abs(dc)
    return total


def analyze_input(grid: Any) -> dict[str, Any]:
    height, width = validate_grid(grid)
    if width < 3:
        raise ValueError("input needs a body area, a gap column, and a key column")

    key_rows_and_colors = [
        (row, grid[row][width - 1])
        for row in range(height)
        if grid[row][width - 1] != 0
    ]
    key_colors = [color for _row, color in key_rows_and_colors]
    if not 2 <= len(key_colors) <= 7:
        raise ValueError("input must contain 2..7 nonzero right-edge keys")
    if len(set(key_colors)) != len(key_colors):
        raise ValueError("right-edge key colors must be distinct")

    body_colors = {value for row in grid for value in row[:-1] if value != 0}
    if body_colors != set(key_colors):
        raise ValueError("body colors must match right-edge key colors exactly")

    shapes: list[dict[str, Any]] = []
    for key_row, color in key_rows_and_colors:
        components = _components(grid, color, body_only=True)
        if len(components) != 1 or len(components[0]) <= 1:
            raise ValueError(f"color {color} must have exactly one multi-cell body")
        if grid[key_row][width - 2] == color:
            raise ValueError(f"color {color} body touches its key")
        cells = components[0]
        shapes.append(
            {
                "color": color,
                "key_row": key_row,
                "cells": cells,
                "size": len(cells),
            }
        )

    return {
        "height": height,
        "width": width,
        "key_colors": key_colors,
        "key_rows": [row for row, _color in key_rows_and_colors],
        "shapes": shapes,
    }


def render_comparison(key_colors: list[int], signatures: list[int]) -> list[list[int]]:
    if len(key_colors) != len(signatures) or not key_colors:
        raise ValueError("key colors and signatures must be non-empty and aligned")
    count = len(key_colors)
    total = 3 * (count + 1) - 1
    result = [[0 for _ in range(total)] for _ in range(total)]
    for row in range(total):
        block_row, local_row = divmod(row, 3)
        for col in range(total):
            block_col, local_col = divmod(col, 3)
            if local_row == 2 or local_col == 2:
                continue
            if block_row == 0 and block_col == 0:
                continue
            if block_row == 0:
                result[row][col] = key_colors[block_col - 1]
            elif block_col == 0:
                result[row][col] = key_colors[block_row - 1]
            elif block_row != block_col:
                result[row][col] = (
                    2
                    if signatures[block_row - 1] == signatures[block_col - 1]
                    else 5
                )
    return result


def output_for(grid: Any, metric: Any) -> list[list[int]]:
    selected = validate_metric(metric)
    analysis = analyze_input(grid)
    signatures = [
        pairwise_signature(shape["cells"], selected) for shape in analysis["shapes"]
    ]
    return render_comparison(analysis["key_colors"], signatures)
