from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Mirror every coloured source left of the full-height 5 divider."""
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
        raise ValueError(f"expected one full-height colour-5 divider, got {divider_columns}")
    divider = divider_columns[0]
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(divider):
            value = grid[row][col]
            if value not in (0, 5):
                target_col = 2 * divider - col
                if 0 <= target_col < width:
                    output[row][target_col] = value
    return output
