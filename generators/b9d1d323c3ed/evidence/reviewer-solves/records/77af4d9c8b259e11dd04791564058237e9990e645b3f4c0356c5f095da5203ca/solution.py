"""Visible-example-only solution for blind task b9d1d323c3ed."""


def solve(grid):
    """Crop the non-background object and duplicate that crop horizontally."""
    rows = [r for r, row in enumerate(grid) for value in row if value != 0]
    cols = [c for row in grid for c, value in enumerate(row) if value != 0]
    if not rows or not cols:
        return []
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
    return [row + row for row in crop]
