from __future__ import annotations

from copy import deepcopy


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Raise each colored marker on the horizontal 1-line into a capped pole.

    Visible examples establish fixed pole heights for the only marker colors:
    red (2) is four cells above the baseline; azure (8) is three.  The top cell
    keeps the marker color and intervening cells are blue (1).  Adjacent markers
    form adjacent poles, so runs naturally become rectangular comb teeth.
    """
    out = deepcopy(grid)
    if not grid or not grid[0]:
        return out

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    marker_heights = {2: 4, 8: 3}

    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            height = marker_heights.get(color)
            if height is None:
                continue

            top = r - height
            if top < 0:
                # The visible tasks leave enough room.  Clipping is safer than
                # wrapping via negative indices on any malformed variant.
                top = 0
            for rr in range(top, r):
                out[rr][c] = color if rr == top else 1

    return out
