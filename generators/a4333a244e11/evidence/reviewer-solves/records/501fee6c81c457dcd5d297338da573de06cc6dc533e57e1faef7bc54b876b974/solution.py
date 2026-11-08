"""Visible-example solution for a4333a244e11."""
from __future__ import annotations

from copy import deepcopy


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill each framed interior zero from its Manhattan-nearest colored seed.

    The color-8 frame and the exterior remain unchanged.  Exact distance ties
    remain zero, matching the visible diagonal and symmetric examples.
    """
    output = deepcopy(grid)
    frame_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    ]
    if not frame_cells:
        return output

    top = min(row for row, _ in frame_cells)
    bottom = max(row for row, _ in frame_cells)
    left = min(col for _, col in frame_cells)
    right = max(col for _, col in frame_cells)
    seeds = [
        (row, col, grid[row][col])
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if grid[row][col] not in (0, 8)
    ]
    if len(seeds) != 2:
        return output

    first, second = seeds
    for row in range(top + 1, bottom):
        for col in range(left + 1, right):
            if grid[row][col] != 0:
                continue
            d1 = abs(row - first[0]) + abs(col - first[1])
            d2 = abs(row - second[0]) + abs(col - second[1])
            if d1 < d2:
                output[row][col] = first[2]
            elif d2 < d1:
                output[row][col] = second[2]
            # Ties intentionally stay background (0).
    return output
