"""Blind solve for task 55cfa127936a.

Keep only the uppermost non-background cell in each column.
"""


def solve(grid):
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    for c in range(width):
        for r in range(height):
            if grid[r][c] != 0:
                out[r][c] = grid[r][c]
                break
    return out
