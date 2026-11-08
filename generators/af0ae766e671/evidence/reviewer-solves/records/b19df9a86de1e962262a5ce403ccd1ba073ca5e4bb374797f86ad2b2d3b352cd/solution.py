"""Visible-example solution; no generator, reference, or private-data imports."""


def solve(grid):
    if not grid or len(grid) % 2:
        raise ValueError("expected a nonempty grid with two equal-height panels")
    width = len(grid[0])
    if not width or any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    half = len(grid) // 2
    return [
        [6 if (grid[row][column] != 0) != (grid[row + half][column] != 0)
         else 0 for column in range(width)]
        for row in range(half)
    ]
