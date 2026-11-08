"""Visible-example solution for blind task ce99418cc163."""


def solve(grid):
    """Complete three-corner rectangles of color 2 with color 3.

    The search is based only on the original grid: a newly added green corner
    cannot create another candidate.  A non-background fourth corner is left
    unchanged.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for top in range(height):
        for bottom in range(top + 1, height):
            for left in range(width):
                for right in range(left + 1, width):
                    corners = (
                        (top, left),
                        (top, right),
                        (bottom, left),
                        (bottom, right),
                    )
                    is_red = [grid[row][col] == 2 for row, col in corners]
                    if sum(is_red) != 3:
                        continue
                    missing = is_red.index(False)
                    row, col = corners[missing]
                    if grid[row][col] == 0:
                        out[row][col] = 3

    return out
