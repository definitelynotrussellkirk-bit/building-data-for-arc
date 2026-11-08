"""Visible-example solution for the generated ARC lesson."""
from __future__ import annotations

from itertools import combinations


def solve(grid):
    """Recolor exact copies of the color-8 tile and bridges between them."""
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    tile_rows = (h + 1) // 4
    tile_cols = (w + 1) // 4

    def mask(tr, tc):
        return tuple(
            grid[1 + 4 * tr + dr][1 + 4 * tc + dc] != 0
            for dr in range(3)
            for dc in range(3)
        )

    def values(tr, tc):
        return tuple(
            grid[1 + 4 * tr + dr][1 + 4 * tc + dc]
            for dr in range(3)
            for dc in range(3)
        )

    positions = [(tr, tc) for tr in range(tile_rows) for tc in range(tile_cols)]
    seed = next(pos for pos in positions if 8 in values(*pos))
    key_mask = mask(*seed)
    keys = {pos for pos in positions if mask(*pos) == key_mask}

    bridges = set()
    for a, b in combinations(sorted(keys), 2):
        if a[0] == b[0]:
            bridges.update((a[0], tc) for tc in range(min(a[1], b[1]) + 1, max(a[1], b[1])))
        if a[1] == b[1]:
            bridges.update((tr, a[1]) for tr in range(min(a[0], b[0]) + 1, max(a[0], b[0])))
    bridges -= keys

    for tr, tc in positions:
        color = 8 if (tr, tc) in keys else 7 if (tr, tc) in bridges else None
        if color is None:
            continue
        for dr in range(3):
            for dc in range(3):
                r, c = 1 + 4 * tr + dr, 1 + 4 * tc + dc
                if out[r][c] != 0:
                    out[r][c] = color
    return out
