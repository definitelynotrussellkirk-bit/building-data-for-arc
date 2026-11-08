"""Blind solution for task d0d18b0499a5.

For every row containing exactly two non-zero cells, replace the inclusive
horizontal span between them with color 8.  All other cells become background.
"""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    for row_index, row in enumerate(grid):
        occupied = [column for column, value in enumerate(row) if value != 0]
        if len(occupied) == 2:
            left, right = occupied
            for column in range(left, right + 1):
                out[row_index][column] = 8

    return out
