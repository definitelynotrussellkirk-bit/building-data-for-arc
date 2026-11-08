"""Visible-only ARC solve for task cc74d7392ecd.

Each non-background singleton is expanded to its orthogonal radius-1 cross.
Cells beyond the grid boundary are clipped.
"""


def solve(grid):
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    for row in range(height):
        if len(grid[row]) != width:
            raise ValueError("grid must be rectangular")
        for col, color in enumerate(grid[row]):
            if color == 0:
                continue
            for drow, dcol in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = row + drow, col + dcol
                if 0 <= rr < height and 0 <= cc < width:
                    out[rr][cc] = color
    return out
