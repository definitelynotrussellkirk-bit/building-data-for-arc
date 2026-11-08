from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Remove the left instruction column, then rotate rows by its blue marker.

    The unique color-2 cell in the first column gives the number of rows to
    move from the bottom of the cropped square to its top.  A marker in row 0
    therefore leaves the cropped grid unchanged.
    """
    if not grid or not grid[0]:
        return []

    marker_row = next((r for r, row in enumerate(grid) if row[0] == 2), 0)
    cropped = [row[1:] for row in grid]
    if not cropped:
        return []

    shift = marker_row % len(cropped)
    if shift == 0:
        return cropped
    return cropped[-shift:] + cropped[:-shift]
