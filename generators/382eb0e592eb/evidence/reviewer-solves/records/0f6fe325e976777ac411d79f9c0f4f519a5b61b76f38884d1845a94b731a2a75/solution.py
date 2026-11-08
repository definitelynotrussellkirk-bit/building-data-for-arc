from __future__ import annotations


def solve(grid):
    """Copy every equal nonzero horizontal pair one row downward.

    Pair detection uses the original input, so a length-three run copies all
    three cells and newly painted cells do not create recursive triggers.
    Pairs already on the bottom row are inert.
    """
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if any(not isinstance(row, list) or not row for row in grid):
        raise ValueError("rows must be nonempty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    output = [list(row) for row in grid]
    for row in range(len(grid) - 1):
        for col in range(width - 1):
            value = grid[row][col]
            if value != 0 and grid[row][col + 1] == value:
                output[row + 1][col] = value
                output[row + 1][col + 1] = value
    return output
