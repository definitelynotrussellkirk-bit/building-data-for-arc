from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Overlay the two panels around the middle separator row.

    A cell is 3 when either corresponding panel cell is nonzero; otherwise it
    is 0.  The visible tasks have two equally sized panels separated by one
    full-width row.
    """
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if len(grid) % 2 != 1:
        raise ValueError("expected two equal-height panels and one separator row")

    half = len(grid) // 2
    top = grid[:half]
    bottom = grid[half + 1 :]
    if len(top) != len(bottom):
        raise ValueError("panel heights differ")

    return [
        [3 if top_value != 0 or bottom_value != 0 else 0
         for top_value, bottom_value in zip(top_row, bottom_row)]
        for top_row, bottom_row in zip(top, bottom)
    ]
