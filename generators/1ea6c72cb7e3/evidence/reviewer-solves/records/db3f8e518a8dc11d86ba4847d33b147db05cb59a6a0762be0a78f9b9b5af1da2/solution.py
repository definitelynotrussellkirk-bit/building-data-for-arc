"""Example-derived wall-segment voting solver; no task/runtime imports."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Preserve nonzero cells and combine colors in row/column wall segments."""
    if not isinstance(grid, list):
        raise ValueError('grid must be a list of rows')
    if not grid:
        return []
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError('rows must be nonempty lists')
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError('grid must be rectangular')
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        raise ValueError('colors must be integers in 0..9')

    votes = [[0] * w for _ in range(h)]

    # Every non-wall cell in one uninterrupted horizontal segment has access
    # to the same original colors. Sources do not themselves end the segment.
    for r in range(h):
        start = 0
        while start < w:
            if grid[r][start] == 5:
                start += 1
                continue
            end, mask = start, 0
            while end < w and grid[r][end] != 5:
                if grid[r][end] != 0:
                    mask |= 1 << grid[r][end]
                end += 1
            for c in range(start, end):
                votes[r][c] |= mask
            start = end

    for c in range(w):
        start = 0
        while start < h:
            if grid[start][c] == 5:
                start += 1
                continue
            end, mask = start, 0
            while end < h and grid[end][c] != 5:
                if grid[end][c] != 0:
                    mask |= 1 << grid[end][c]
                end += 1
            for r in range(start, end):
                votes[r][c] |= mask
            start = end

    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            mask = votes[r][c]
            if mask == 0:
                out[r][c] = 0
            elif mask & (mask - 1):
                out[r][c] = 8
            else:
                out[r][c] = mask.bit_length() - 1
    return out
