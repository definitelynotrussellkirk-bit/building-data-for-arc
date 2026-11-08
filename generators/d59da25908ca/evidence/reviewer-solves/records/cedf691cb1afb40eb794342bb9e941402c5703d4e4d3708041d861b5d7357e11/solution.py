"""Visible-only ARC solution for the blind pre-repair episode."""


def solve(grid):
    """Recolor every maximal vertical run of exactly two 3-cells to 7."""
    out = [row[:] for row in grid]
    if not grid:
        return out
    height = len(grid)
    width = len(grid[0])

    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 3:
                row += 1
                continue
            start = row
            while row < height and grid[row][col] == 3:
                row += 1
            if row - start == 2:
                out[start][col] = 7
                out[start + 1][col] = 7
    return out
