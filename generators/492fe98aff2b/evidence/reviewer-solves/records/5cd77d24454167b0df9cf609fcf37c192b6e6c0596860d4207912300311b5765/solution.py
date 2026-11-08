from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop to the smallest rectangle containing every non-background cell."""
    occupied = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return [row[:] for row in grid]

    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(column for _, column in occupied)
    right = max(column for _, column in occupied)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]
