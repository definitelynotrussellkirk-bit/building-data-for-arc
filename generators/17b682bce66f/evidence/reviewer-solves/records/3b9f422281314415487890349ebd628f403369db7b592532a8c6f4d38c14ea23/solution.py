"""Example-based rotation/stamping solver.

The reviewer saw the task's rule before this episode, not during it. Visible
pairs identify the rotations, but do not uniquely establish collision priority.
Only solve(grid) is used at execution time; this module reads no files.
"""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("Expected integer colors from 0 through 9")
    height, width = len(grid), len(grid[0])
    references = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(references) != 1:
        raise ValueError("Expected exactly one reference marker of color 9")
    origin_r, origin_c = references[0]
    offsets = [(r - origin_r, c - origin_c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 8]
    if not offsets:
        raise ValueError("Expected a source shape of color 8")

    result = [[0] * width for _ in range(height)]
    # Row-major sequential writing is an assumption not uniquely identified by
    # this episode's demonstrations. See public_probe.json for rival policies.
    for row_index, row in enumerate(grid):
        for col_index, color in enumerate(row):
            if color not in (2, 3, 4, 5):
                continue
            result[row_index][col_index] = color
            for dr, dc in offsets:
                for _ in range(color - 2):
                    dr, dc = dc, -dr  # Clockwise in row/column coordinates.
                rr, cc = row_index + dr, col_index + dc
                if 0 <= rr < height and 0 <= cc < width:
                    result[rr][cc] = color + 2
    return result
