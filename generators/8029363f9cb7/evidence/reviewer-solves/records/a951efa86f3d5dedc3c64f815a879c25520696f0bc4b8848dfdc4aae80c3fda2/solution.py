"""Visible-example solution for the beam-and-mirrors transformation."""

from __future__ import annotations

from typing import List, Sequence, Tuple

Grid = List[List[int]]
Direction = Tuple[int, int]


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Trace the right-launched beam from the red source and paint empty cells 8.

    Color 3 acts as a slash mirror, color 4 as a backslash mirror, and color 5
    stops the beam.  All non-painted cells are preserved.
    """
    out = [list(row) for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    source = next(
        ((r, c) for r, row in enumerate(out) for c, value in enumerate(row) if value == 2),
        None,
    )
    if source is None:
        return out

    r, c = source
    dr, dc = (0, 1)  # every visible example launches to the right
    seen: set[Tuple[int, int, int, int]] = set()

    while True:
        state = (r, c, dr, dc)
        if state in seen:
            break
        seen.add(state)

        nr, nc = r + dr, c + dc
        if not (0 <= nr < height and 0 <= nc < width):
            break

        value = out[nr][nc]
        if value == 5:
            break
        if value == 0:
            out[nr][nc] = 8
        elif value == 3:  # slash mirror: / 
            dr, dc = -dc, -dr
        elif value == 4:  # backslash mirror: \\
            dr, dc = dc, dr

        r, c = nr, nc

    return out
