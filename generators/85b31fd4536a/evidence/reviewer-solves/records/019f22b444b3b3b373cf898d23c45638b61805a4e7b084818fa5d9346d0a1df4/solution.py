from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Apply the binary panel on the left as a mask to the color panel."""
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separators = [
        column
        for column in range(width)
        if all(row[column] == 9 for row in grid)
    ]
    if len(separators) != 1:
        raise ValueError("expected exactly one full-height separator of color 9")

    separator = separators[0]
    left_width = separator
    right_width = width - separator - 1
    if left_width != right_width:
        raise ValueError("mask and color panels must have equal widths")

    return [
        [color if mask == 1 else 0 for mask, color in zip(row[:separator], row[separator + 1 :])]
        for row in grid
    ]
