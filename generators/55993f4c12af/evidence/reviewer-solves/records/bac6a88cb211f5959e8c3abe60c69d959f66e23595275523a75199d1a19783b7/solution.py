"""Visible-example hypothesis: Boolean union of vertically stacked panels."""

def solve(grid):
    if not grid or len(grid) % 2 or not grid[0]:
        raise ValueError("Expected two nonempty equal-height panels")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")
    half = len(grid) // 2
    return [[4 if grid[r][c] != 0 or grid[r + half][c] != 0 else 0
             for c in range(width)] for r in range(half)]
