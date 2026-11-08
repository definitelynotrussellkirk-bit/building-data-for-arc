"""Visible-example solution for the reviewer-authored ARC episode."""
from __future__ import annotations


def solve(grid):
    """Replace each nonzero cell by a cyan four-neighbour halo."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0:
                continue
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = row + drow, col + dcol
                if 0 <= rr < height and 0 <= cc < width:
                    out[rr][cc] = 8
    return out
