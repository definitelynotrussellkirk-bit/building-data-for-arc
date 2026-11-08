from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Rotate every non-background cell 90° clockwise around the unique 9 pivot."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    pivots = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    if len(pivots) != 1:
        raise ValueError(f"expected exactly one color-9 pivot, found {len(pivots)}")

    pivot_row, pivot_col = pivots[0]
    result = [[0 for _ in range(width)] for _ in range(height)]

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0:
                continue

            delta_row = row - pivot_row
            delta_col = col - pivot_col
            rotated_row = pivot_row + delta_col
            rotated_col = pivot_col - delta_row

            if not (0 <= rotated_row < height and 0 <= rotated_col < width):
                raise ValueError(
                    "clockwise rotation moves a colored cell outside the grid: "
                    f"source={(row, col)}, target={(rotated_row, rotated_col)}"
                )
            result[rotated_row][rotated_col] = value

    return result
