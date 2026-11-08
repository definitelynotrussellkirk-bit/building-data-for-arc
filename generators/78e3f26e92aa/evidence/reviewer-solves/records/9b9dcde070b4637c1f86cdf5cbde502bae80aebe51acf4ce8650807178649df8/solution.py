from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend each same-colour bar pair into height-scaled outward rays.

    Each nonzero colour forms two equal vertical bars.  At every full bar-height
    step above or below the source bars, the left ray moves one column left and
    the right ray moves one column right.  A cell reached by both colours is 6.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    colours = sorted({value for row in grid for value in row if value != 0})
    for colour in colours:
        cells = [
            (row_index, col_index)
            for row_index, row in enumerate(grid)
            for col_index, value in enumerate(row)
            if value == colour
        ]
        if not cells:
            continue

        columns = sorted({col for _, col in cells})
        rows = sorted({row for row, _ in cells})
        if len(columns) != 2 or not rows:
            raise ValueError(f"colour {colour} is not a pair of vertical bars")

        top, bottom = rows[0], rows[-1]
        bar_height = bottom - top + 1
        expected = {(row, col) for row in range(top, bottom + 1) for col in columns}
        if set(cells) != expected:
            raise ValueError(f"colour {colour} does not form two equal solid bars")

        left, right = columns
        for row in range(height):
            if row < top:
                step = (top - row - 1) // bar_height + 1
            elif row > bottom:
                step = (row - bottom - 1) // bar_height + 1
            else:
                step = 0

            for col in (left - step, right + step):
                if not (0 <= col < width):
                    continue
                if out[row][col] == 0 or out[row][col] == colour:
                    out[row][col] = colour
                else:
                    out[row][col] = 6

    return out
