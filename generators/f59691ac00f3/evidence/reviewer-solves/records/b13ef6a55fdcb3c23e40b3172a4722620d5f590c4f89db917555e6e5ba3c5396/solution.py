"""Blind solution for task f59691ac00f3."""


def solve(grid):
    """Grow successive inward rows from colored pairs two columns apart.

    A cell one row below is colored when its upper-left and upper-right
    neighbors (distance two) are both non-background.  Its color is the
    2<->5 complement of the upper-left neighbor.  All other cells remain 7.
    """
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [list(row) for row in grid]

    for r in range(1, height):
        previous = out[r - 1]
        current = [7] * width
        for c in range(1, width - 1):
            left = previous[c - 1]
            right = previous[c + 1]
            if left != 7 and right != 7:
                current[c] = 5 if left == 2 else 2
        out[r] = current
    return out
