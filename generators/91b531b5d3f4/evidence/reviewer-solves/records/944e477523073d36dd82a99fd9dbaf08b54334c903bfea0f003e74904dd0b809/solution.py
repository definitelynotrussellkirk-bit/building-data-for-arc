"""Visible-example-only solution for the blind ARC episode."""


def solve(grid):
    """Recolor marker cells (1) from the nonzero header in their column."""
    if not grid:
        return []
    header = grid[0]
    return [
        [header[c] if value == 1 and header[c] != 0 else value
         for c, value in enumerate(row)]
        for row in grid
    ]
