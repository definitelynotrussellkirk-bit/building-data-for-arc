from __future__ import annotations


def solve(grid):
    """Scatter the fixed 2x2 block at rows/cols 1..2 to the output corners."""
    if not isinstance(grid, (list, tuple)) or len(grid) < 3:
        raise ValueError("expected at least three rows")
    if not isinstance(grid[0], (list, tuple)) or len(grid[0]) < 3:
        raise ValueError("expected at least three columns")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")

    height = len(grid)
    output = [[0 for _ in range(width)] for _ in range(height)]
    output[0][0] = grid[1][1]
    output[0][-1] = grid[1][2]
    output[-1][0] = grid[2][1]
    output[-1][-1] = grid[2][2]
    return output
