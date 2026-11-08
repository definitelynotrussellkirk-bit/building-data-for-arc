from __future__ import annotations


def _solid_tile_origins(grid):
    height = len(grid)
    width = len(grid[0])
    return [
        (row, col)
        for row in range(height - 2)
        for col in range(width - 2)
        if all(grid[row + dr][col + dc] != 0 for dr in range(3) for dc in range(3))
    ]


def solve(grid):
    """Arrange the scattered 3x3 glyph tiles into a 9x9 compass."""
    output = [[5 for _ in range(9)] for _ in range(9)]

    # Each nonblank tile's non-gray cells form the same local compass glyph as
    # its target macro-position.  The all-gray tile represents the gray center.
    shape_to_target = {
        frozenset({(0, 0), (0, 1), (1, 0)}): (0, 0),
        frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}): (0, 1),
        frozenset({(0, 1), (0, 2), (1, 2)}): (0, 2),
        frozenset({(0, 0), (1, 0), (1, 1), (2, 0)}): (1, 0),
        frozenset({(0, 2), (1, 1), (1, 2), (2, 2)}): (1, 2),
        frozenset({(1, 0), (2, 0), (2, 1)}): (2, 0),
        frozenset({(1, 1), (2, 0), (2, 1), (2, 2)}): (2, 1),
        frozenset({(1, 2), (2, 1), (2, 2)}): (2, 2),
    }

    origins = _solid_tile_origins(grid)
    if len(origins) != 9:
        raise ValueError(f"expected nine solid 3x3 tiles, found {len(origins)}")

    for top, left in origins:
        tile = [[grid[top + dr][left + dc] for dc in range(3)] for dr in range(3)]
        signal_shape = frozenset(
            (dr, dc)
            for dr in range(3)
            for dc in range(3)
            if tile[dr][dc] != 5
        )
        if not signal_shape:
            continue
        target = shape_to_target.get(signal_shape)
        if target is None:
            raise ValueError(f"unknown glyph shape: {sorted(signal_shape)}")
        out_top, out_left = 3 * target[0], 3 * target[1]
        for dr in range(3):
            for dc in range(3):
                output[out_top + dr][out_left + dc] = tile[dr][dc]

    return output
