def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transform(shape, marker):
    if marker == 1:      # unchanged
        return [row[:] for row in shape]
    if marker == 3:      # quarter-turn clockwise
        return _rotate_cw(shape)
    if marker == 4:      # half-turn
        return [row[::-1] for row in shape[::-1]]
    if marker == 6:      # left-right reflection
        return [row[::-1] for row in shape]
    raise ValueError(f"unexpected marker color: {marker}")


def solve(grid):
    # Crop the blue motif and recolor it to orange (7).
    blue = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == 2]
    if not blue:
        raise ValueError("missing blue motif")
    r0, r1 = min(r for r, _ in blue), max(r for r, _ in blue)
    c0, c1 = min(c for _, c in blue), max(c for _, c in blue)
    shape = [
        [7 if grid[r][c] == 2 else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]

    # The four marker colors occupy the corners of a 2x2 template.  Each
    # marker selects the corresponding orientation of the motif.
    markers = [(r, c, value)
               for r, row in enumerate(grid)
               for c, value in enumerate(row)
               if value in {1, 3, 4, 6}]
    rows = sorted({r for r, _, _ in markers})
    cols = sorted({c for _, c, _ in markers})
    if len(markers) != 4 or len(rows) != 2 or len(cols) != 2:
        raise ValueError("expected four corner markers")
    marker_at = {(r, c): value for r, c, value in markers}

    tiles = [[_transform(shape, marker_at[(r, c)]) for c in cols] for r in rows]
    tile_h = len(tiles[0][0])
    tile_w = len(tiles[0][0][0])
    if any(len(tile) != tile_h or any(len(row) != tile_w for row in tile)
           for tile_row in tiles for tile in tile_row):
        raise ValueError("transformed motif tiles have incompatible dimensions")

    out = []
    for tile_row in tiles:
        for i in range(tile_h):
            out.append(tile_row[0][i] + [0] + tile_row[1][i])
        if tile_row is tiles[0]:
            out.append([0] * (2 * tile_w + 1))
    return out
