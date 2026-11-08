from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Reflect every non-background cell across both grid midlines."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0:
                continue
            for rr in (r, height - 1 - r):
                for cc in (c, width - 1 - c):
                    out[rr][cc] = value
    return out
