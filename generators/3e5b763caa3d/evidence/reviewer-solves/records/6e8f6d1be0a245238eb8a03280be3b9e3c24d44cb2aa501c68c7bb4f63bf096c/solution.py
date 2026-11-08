from __future__ import annotations


def solve(grid):
    """Mirror nonzero cells left of the unique uniform divider column."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    divider_columns = []
    for column in range(width):
        color = grid[0][column]
        if color != 0 and all(grid[row][column] == color for row in range(height)):
            divider_columns.append(column)

    if len(divider_columns) != 1:
        raise ValueError("expected one full-height uniform nonzero divider column")
    axis = divider_columns[0]

    output = [list(row) for row in grid]
    for row in range(height):
        for column in range(axis):
            value = grid[row][column]
            reflected = 2 * axis - column
            if value != 0 and 0 <= reflected < width:
                output[row][reflected] = value
    return output
