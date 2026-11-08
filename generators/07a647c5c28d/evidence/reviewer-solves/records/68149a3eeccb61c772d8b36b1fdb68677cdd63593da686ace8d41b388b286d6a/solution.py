from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Crop the grid to the minimal rectangle containing every color-6 cell."""
    points = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == 6
    ]
    if not points:
        return []

    top = min(row for row, _ in points)
    bottom = max(row for row, _ in points)
    left = min(column for _, column in points)
    right = max(column for _, column in points)
    return [list(row[left : right + 1]) for row in grid[top : bottom + 1]]
