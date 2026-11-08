"""Visible-example solution for d476983a3d6c."""
from __future__ import annotations


def solve(grid):
    out = [row[:] for row in grid]
    command = grid[0][0]

    ordered_colors = []
    seen = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (r, c) == (0, 0) or value == 0 or value in seen:
                continue
            seen.add(value)
            ordered_colors.append(value)

    for color in ordered_colors:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if command == 1:
            cstep = 1 if c2 >= c1 else -1
            for c in range(c1, c2 + cstep, cstep):
                out[r1][c] = color
            rstep = 1 if r2 >= r1 else -1
            for r in range(r1, r2 + rstep, rstep):
                out[r][c2] = color
        elif command == 2:
            rstep = 1 if r2 >= r1 else -1
            for r in range(r1, r2 + rstep, rstep):
                out[r][c1] = color
            cstep = 1 if c2 >= c1 else -1
            for c in range(c1, c2 + cstep, cstep):
                out[r2][c] = color
        else:
            raise ValueError(f"unsupported command {command!r}")
    return out
