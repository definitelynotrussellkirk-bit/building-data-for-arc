"""Visible-example solution for task 0be8ff9b4144."""


def solve(grid):
    out = [row[:] for row in grid]
    active_rows = [r for r in range(1, len(grid)) if grid[r][0] == 3]
    active_cols = [c for c in range(1, len(grid[0])) if grid[0][c] == 2]
    for r in active_rows:
        for c in active_cols:
            out[r][c] = 5
    return out
