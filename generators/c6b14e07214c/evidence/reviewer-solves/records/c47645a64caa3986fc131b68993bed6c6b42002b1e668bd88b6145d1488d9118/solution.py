"""Visible-example hypothesis: nearest seed by taxicab distance, low-color ties.

Written during the fresh solve phase. No generator/reference imports or labels.
"""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('a nonempty rectangular grid is required')
    frame_cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
    if not frame_cells:
        raise ValueError('no frame color was found')
    top = min(r for r, c in frame_cells)
    bottom = max(r for r, c in frame_cells)
    left = min(c for r, c in frame_cells)
    right = max(c for r, c in frame_cells)
    seeds = [(r, c, grid[r][c]) for r in range(top+1, bottom)
             for c in range(left+1, right) if grid[r][c] not in (0, 7)]
    if not seeds:
        raise ValueError('no interior source colors were found')
    result = [row[:] for row in grid]
    for r in range(top+1, bottom):
        for c in range(left+1, right):
            if grid[r][c] != 0:
                continue
            source = min(seeds, key=lambda p: (abs(p[0]-r)+abs(p[1]-c), p[2], p[0], p[1]))
            result[r][c] = source[2]
    return result
