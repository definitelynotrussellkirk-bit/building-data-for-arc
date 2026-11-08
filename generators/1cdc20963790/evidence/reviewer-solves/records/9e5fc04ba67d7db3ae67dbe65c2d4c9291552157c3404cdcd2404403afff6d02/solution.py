from __future__ import annotations


def solve(grid):
    """Keep the headers; dispatch 1 from the row key and 2 from the column key."""
    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]
    out[0] = list(grid[0])
    for row in range(1, height):
        out[row][0] = grid[row][0]
        for col in range(1, width):
            if grid[row][col] == 1:
                out[row][col] = grid[row][0]
            elif grid[row][col] == 2:
                out[row][col] = grid[0][col]
    return out
