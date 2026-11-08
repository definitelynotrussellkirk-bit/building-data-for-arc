"""Visible-example solution for reviewer episode cfd0943c5b14."""


def solve(grid):
    """Replace every nonzero cell by a clipped cyan diagonal-X stamp."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    for row in range(height):
        if len(grid[row]) != width:
            raise ValueError("grid must be rectangular")
        for col, value in enumerate(grid[row]):
            if value == 0:
                continue
            for dr, dc in ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)):
                rr, cc = row + dr, col + dc
                if 0 <= rr < height and 0 <= cc < width:
                    out[rr][cc] = 8
    return out
