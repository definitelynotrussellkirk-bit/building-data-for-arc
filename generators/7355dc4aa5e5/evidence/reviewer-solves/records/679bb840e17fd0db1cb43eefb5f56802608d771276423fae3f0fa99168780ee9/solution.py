"""Visible-example solution for the prepared 7355dc4aa5e5 episode."""


def solve(grid):
    """Expand each original blue marker into a cross and diagonal stamp."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    result = [list(row) for row in grid]

    for row, col in markers:
        for other_col in range(width):
            result[row][other_col] = 1
        for other_row in range(height):
            result[other_row][col] = 1
        result[row][col] = 2
        for row_delta, col_delta in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            neighbor_row = row + row_delta
            neighbor_col = col + col_delta
            if 0 <= neighbor_row < height and 0 <= neighbor_col < width:
                result[neighbor_row][neighbor_col] = 3

    return result
