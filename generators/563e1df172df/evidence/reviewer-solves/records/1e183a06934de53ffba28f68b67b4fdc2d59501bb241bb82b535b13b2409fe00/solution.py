"""Visible-example solution for reviewer solve 563e1df172df."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Join red 2 to green 3: horizontal on red's row, then vertical."""
    out = [row[:] for row in grid]
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    if len(red) != 1 or len(green) != 1:
        raise ValueError("expected exactly one red(2) and one green(3) cell")

    rr, rc = red[0]
    gr, gc = green[0]

    horizontal_step = 1 if gc > rc else -1
    for c in range(rc + horizontal_step, gc, horizontal_step):
        out[rr][c] = 8

    vertical_step = 1 if gr > rr else -1
    for r in range(rr + vertical_step, gr, vertical_step):
        out[r][gc] = 8

    return out
