"""Visible-example solution for reviewer-authored task 7d8fc2325e02."""


def solve(grid):
    """Overlay nonzero occupancy of rows 0..3 and 5..8 into green 3s."""
    if len(grid) != 9 or not grid or not grid[0]:
        raise ValueError("expected a nonempty 9-row grid")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    return [
        [3 if grid[row][col] != 0 or grid[row + 5][col] != 0 else 0
         for col in range(width)]
        for row in range(4)
    ]
