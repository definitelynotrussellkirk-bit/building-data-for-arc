from __future__ import annotations


def solve(grid):
    """Reflect colored cells across the unique full-height gray divider."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    height = len(grid)
    width = len(grid[0])
    divider_columns = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    if len(divider_columns) != 1:
        raise ValueError(
            f"expected one full-height gray divider, got {divider_columns}"
        )

    divider = divider_columns[0]
    result = [list(row) for row in grid]
    for row in range(height):
        for col in range(divider):
            value = grid[row][col]
            if value in (0, 5):
                continue
            mirror_col = 2 * divider - col
            if 0 <= mirror_col < width:
                result[row][mirror_col] = value
    return result
