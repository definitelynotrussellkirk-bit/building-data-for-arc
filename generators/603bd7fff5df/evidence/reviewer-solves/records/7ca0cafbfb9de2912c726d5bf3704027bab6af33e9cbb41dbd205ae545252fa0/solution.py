from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the gray-marker bbox, keeping one source row above and below."""
    gray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if not gray:
        raise ValueError("input has no gray (5) markers")

    top = min(row for row, _ in gray)
    bottom = max(row for row, _ in gray)
    left = min(col for _, col in gray)
    right = max(col for _, col in gray)
    if top == 0 or bottom == len(grid) - 1:
        raise ValueError("gray bbox lacks the required vertical halo row")

    return [row[left : right + 1] for row in grid[top - 1 : bottom + 2]]
