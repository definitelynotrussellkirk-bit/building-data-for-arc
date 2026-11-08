from __future__ import annotations

import copy


def solve(grid):
    """Fill marker-delimited segments in columns whose last marker is 5."""
    if not grid:
        return []
    output = copy.deepcopy(grid)
    height = len(grid)
    width = len(grid[0])

    for column in range(width):
        markers = [row for row in range(height) if grid[row][column] != 0]
        if not markers or grid[markers[-1]][column] != 5:
            continue

        previous = -1
        for row in markers:
            color = grid[row][column]
            for fill_row in range(previous + 1, row + 1):
                output[fill_row][column] = color
            previous = row

    return output
