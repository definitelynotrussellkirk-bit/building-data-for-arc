from __future__ import annotations


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


def solve(grid):
    """Connect red (2) to blue (1) with the demonstrated ordered green path."""
    red = None
    blue = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                red = (r, c)
            elif value == 1:
                blue = (r, c)

    if red is None or blue is None:
        raise ValueError("expected one red endpoint and one blue endpoint")

    out = [row[:] for row in grid]
    row_delta = blue[0] - red[0]
    col_delta = blue[1] - red[1]
    row_step = _sign(row_delta)
    col_step = _sign(col_delta)
    row_gap = abs(row_delta)
    col_gap = abs(col_delta)
    straight_steps = abs(row_gap - col_gap)
    total_steps = max(row_gap, col_gap)
    row_dominant = row_gap > col_gap

    r, c = red
    for step in range(1, total_steps + 1):
        if step == 1 or step > 1 + straight_steps:
            r += row_step
            c += col_step
        elif row_dominant:
            r += row_step
        else:
            c += col_step

        if (r, c) != blue:
            out[r][c] = 3

    return out
