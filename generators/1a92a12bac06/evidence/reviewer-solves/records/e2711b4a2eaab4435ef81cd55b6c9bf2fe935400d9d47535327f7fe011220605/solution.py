"""Visible-example solution for the reviewer-authored ARC episode."""


def solve(grid):
    """Recolor the lower floor-half of every vertical 2-bar to 8."""
    out = [row[:] for row in grid]
    if not grid:
        return out

    height = len(grid)
    width = len(grid[0])
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 2:
                row += 1
                continue

            start = row
            while row < height and grid[row][col] == 2:
                row += 1
            stop = row

            # A run of length n contributes floor(n / 2) cells, anchored
            # at its bottom. Odd runs leave the middle cell unchanged.
            recolor_start = stop - ((stop - start) // 2)
            for rr in range(recolor_start, stop):
                out[rr][col] = 8

    return out
