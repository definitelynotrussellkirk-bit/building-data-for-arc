from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Use the left panel as a mask over the right panel."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    # The two square panels are separated by a full-height non-background stripe.
    separators = [
        c
        for c in range(width)
        if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(height))
    ]
    if not separators:
        raise ValueError("could not find panel separator")

    separator = min(
        separators,
        key=lambda c: abs(c - (width - 1) / 2),
    )
    left = [row[:separator] for row in grid]
    right = [row[separator + 1 :] for row in grid]
    if len(left[0]) != len(right[0]):
        raise ValueError("left and right panels must have equal widths")

    return [
        [right[r][c] if left[r][c] != 0 else 0 for c in range(len(left[r]))]
        for r in range(height)
    ]
