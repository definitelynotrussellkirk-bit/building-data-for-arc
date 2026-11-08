"""Visible-example solution for task 34f8510e39d0."""


def solve(grid):
    """Recolor the exposed boundary of every green (3) region azure (8).

    A green cell remains green only when all four orthogonal neighbors are also
    green.  All non-green cells are copied unchanged.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 3:
                continue
            interior = (
                row > 0
                and row + 1 < height
                and col > 0
                and col + 1 < width
                and grid[row - 1][col] == 3
                and grid[row + 1][col] == 3
                and grid[row][col - 1] == 3
                and grid[row][col + 1] == 3
            )
            if not interior:
                out[row][col] = 8

    return out
