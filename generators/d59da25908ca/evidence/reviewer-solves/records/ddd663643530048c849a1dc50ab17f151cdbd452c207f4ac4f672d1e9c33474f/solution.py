"""Visible-example solution for d59da25908ca."""
from copy import deepcopy


def solve(grid):
    """Recolor maximal vertical green runs of exact length two from 3 to 7."""
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 3:
                row += 1
                continue
            start = row
            while row < height and grid[row][col] == 3:
                row += 1
            if row - start == 2:
                out[start][col] = 7
                out[start + 1][col] = 7
    return out
