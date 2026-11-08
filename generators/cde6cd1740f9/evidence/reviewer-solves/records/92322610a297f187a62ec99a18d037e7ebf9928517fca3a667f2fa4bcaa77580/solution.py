"""Visible-example solution for the blind ARC episode."""

from math import isqrt


def solve(grid):
    """Pack each vertical stream into a bottom-aligned centered pyramid.

    Nonzero cells in a column are read from top to bottom.  A stream of
    ``k**2`` cells is written, in the same order, into rows of widths
    ``1, 3, ..., 2*k-1`` centered on that column and resting on the bottom
    edge of the grid.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    for column in range(width):
        stream = [grid[row][column] for row in range(height) if grid[row][column] != 0]
        if not stream:
            continue

        levels = isqrt(len(stream))
        if levels * levels != len(stream):
            raise ValueError(
                f"column {column} has {len(stream)} nonzero cells; expected a square count"
            )
        if levels > height:
            raise ValueError(f"column {column} needs {levels} rows in a {height}-row grid")

        index = 0
        top = height - levels
        for level in range(levels):
            row = top + level
            left = column - level
            right = column + level
            if left < 0 or right >= width:
                raise ValueError(
                    f"pyramid for column {column} does not fit width {width} at level {level}"
                )
            for target_column in range(left, right + 1):
                output[row][target_column] = stream[index]
                index += 1

    return output
