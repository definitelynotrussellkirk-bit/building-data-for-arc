from __future__ import annotations


def solve(grid):
    """Expand each original blue anchor into a direction-colored cross."""
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height = len(source)
    width = len(source[0]) if height else 0

    for row in range(height):
        for col in range(width):
            if source[row][col] != 1:
                continue
            if row > 0:
                output[row - 1][col] = 2
            if col > 0:
                output[row][col - 1] = 7
            if col + 1 < width:
                output[row][col + 1] = 6
            if row + 1 < height:
                output[row + 1][col] = 8
    return output
