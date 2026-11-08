"""Visible-example inference: fill blue-enclosed zero centers with azure."""


def solve(grid):
    """Return a fresh grid, replacing 0 with 8 at four-sided blue centers."""
    out = [list(row) for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(1, len(grid[r]) - 1):
            if (
                grid[r][c] == 0
                and grid[r - 1][c] == 1
                and grid[r + 1][c] == 1
                and grid[r][c - 1] == 1
                and grid[r][c + 1] == 1
            ):
                out[r][c] = 8
    return out
