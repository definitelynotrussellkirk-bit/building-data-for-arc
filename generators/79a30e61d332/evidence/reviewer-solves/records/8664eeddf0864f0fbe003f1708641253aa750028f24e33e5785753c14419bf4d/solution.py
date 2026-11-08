from copy import deepcopy
from itertools import combinations


def solve(grid):
    """Apply the visible 3x3-symbol matching and bridge rule."""
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])

    # The examples form a lattice of 3x3 symbols separated by one all-zero
    # row/column, including a zero border.
    tile_rows = (height - 1) // 4
    tile_cols = (width - 1) // 4
    positions = [(tr, tc) for tr in range(tile_rows) for tc in range(tile_cols)]

    def values(tr, tc):
        return tuple(
            grid[1 + 4 * tr + dr][1 + 4 * tc + dc]
            for dr in range(3)
            for dc in range(3)
        )

    def mask(tr, tc):
        return tuple(value != 0 for value in values(tr, tc))

    seed_tiles = [position for position in positions if 8 in values(*position)]
    if len(seed_tiles) != 1:
        raise ValueError(f"expected one color-8 seed symbol, found {len(seed_tiles)}")

    key_mask = mask(*seed_tiles[0])
    keys = [position for position in positions if mask(*position) == key_mask]
    key_set = set(keys)

    bridges = set()
    for (r1, c1), (r2, c2) in combinations(keys, 2):
        if r1 == r2:
            bridges.update((r1, col) for col in range(min(c1, c2) + 1, max(c1, c2)))
        if c1 == c2:
            bridges.update((row, c1) for row in range(min(r1, r2) + 1, max(r1, r2)))

    for tr, tc in positions:
        color = 8 if (tr, tc) in key_set else 7 if (tr, tc) in bridges else None
        if color is None:
            continue
        for dr in range(3):
            for dc in range(3):
                row = 1 + 4 * tr + dr
                col = 1 + 4 * tc + dc
                if out[row][col] != 0:
                    out[row][col] = color
    return out
