"""Visible-example solution for review task cbe60e2c4b18."""


def solve(grid):
    """Overlay the two divider-separated panels and mark their intersection.

    The input contains two equal-width panels separated by a vertical column of
    color 9.  Return a grid the size of one panel, using color 8 exactly where
    both aligned panel cells are nonzero and 0 elsewhere.
    """
    if not grid:
        return []

    try:
        divider = grid[0].index(9)
    except ValueError as exc:
        raise ValueError("input has no color-9 divider") from exc

    right_start = divider + 1
    right_width = len(grid[0]) - right_start
    if divider != right_width:
        raise ValueError("divider does not separate equal-width panels")

    output = []
    for row in grid:
        if len(row) != len(grid[0]) or row[divider] != 9:
            raise ValueError("input is not a rectangular two-panel grid")
        left = row[:divider]
        right = row[right_start:]
        output.append([
            8 if left_value != 0 and right_value != 0 else 0
            for left_value, right_value in zip(left, right)
        ])
    return output
