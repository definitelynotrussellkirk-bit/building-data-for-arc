def solve(grid):
    """Expand the blue object into four transformed copies selected by markers."""
    blue = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not blue:
        return []

    r0 = min(r for r, _ in blue)
    r1 = max(r for r, _ in blue)
    c0 = min(c for _, c in blue)
    c1 = max(c for _, c in blue)
    tile = [
        [7 if grid[r][c] == 2 else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]

    markers = {
        value: (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in {1, 3, 4, 6}
    }
    marker_rows = sorted({r for r, _ in markers.values()})
    marker_cols = sorted({c for _, c in markers.values()})

    height = len(tile)
    width = len(tile[0])
    result = [[0] * (2 * width + 1) for _ in range(2 * height + 1)]

    def transform(marker):
        rows = tile[::-1] if marker in {3, 4} else tile
        return [row[::-1] for row in rows] if marker in {4, 6} else [row[:] for row in rows]

    for marker, (r, c) in markers.items():
        quadrant_r = marker_rows.index(r)
        quadrant_c = marker_cols.index(c)
        transformed = transform(marker)
        out_r = quadrant_r * (height + 1)
        out_c = quadrant_c * (width + 1)
        for dr, row in enumerate(transformed):
            result[out_r + dr][out_c : out_c + width] = row

    return result
