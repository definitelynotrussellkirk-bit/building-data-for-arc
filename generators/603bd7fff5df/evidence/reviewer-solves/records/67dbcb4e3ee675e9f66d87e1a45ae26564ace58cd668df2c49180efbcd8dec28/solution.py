"""Visible-example solution for reviewer solve task 603bd7fff5df."""


def solve(grid):
    """Crop to the gray (5) columns and one row beyond its vertical span."""
    gray = [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == 5
    ]
    if not gray:
        raise ValueError("expected at least one gray marker")

    top = min(row for row, _ in gray)
    bottom = max(row for row, _ in gray)
    left = min(col for _, col in gray)
    right = max(col for _, col in gray)

    crop_top = top - 1
    crop_bottom = bottom + 1
    if crop_top < 0 or crop_bottom >= len(grid):
        raise ValueError("gray span must have one source row above and below")

    return [row[left : right + 1] for row in grid[crop_top : crop_bottom + 1]]
