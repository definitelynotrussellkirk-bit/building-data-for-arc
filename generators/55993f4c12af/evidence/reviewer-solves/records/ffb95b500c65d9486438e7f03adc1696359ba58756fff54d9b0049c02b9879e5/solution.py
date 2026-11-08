"""Visible-example solution for blind task 55993f4c12af."""


def solve(grid):
    """Overlay the two equal-height panels and recolor their union with 4."""
    height = len(grid)
    if height == 0 or height % 2:
        raise ValueError("expected two non-empty panels of equal height")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    half = height // 2
    return [
        [4 if grid[r][c] != 0 or grid[r + half][c] != 0 else 0 for c in range(width)]
        for r in range(half)
    ]
