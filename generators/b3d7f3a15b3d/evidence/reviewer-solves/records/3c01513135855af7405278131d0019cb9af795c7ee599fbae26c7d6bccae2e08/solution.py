from collections import Counter, defaultdict


def _runs(indices):
    """Return inclusive contiguous runs from an ordered sequence of indices."""
    indices = list(indices)
    if not indices:
        return []
    runs = []
    start = prev = indices[0]
    for value in indices[1:]:
        if value != prev + 1:
            runs.append((start, prev))
            start = value
        prev = value
    runs.append((start, prev))
    return runs


def solve(grid):
    """Complete horizontal/vertical marker lines across the repeated tile array."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    # The repeated tiles are separated by solid background rows and columns.
    # The top-left pixel is on that separator frame in every visible example.
    background = grid[0][0]
    tile_rows = _runs(
        r for r in range(height) if any(grid[r][c] != background for c in range(width))
    )
    tile_cols = _runs(
        c for c in range(width) if any(grid[r][c] != background for r in range(height))
    )
    if not tile_rows or not tile_cols:
        return out

    tile_h = tile_rows[0][1] - tile_rows[0][0] + 1
    tile_w = tile_cols[0][1] - tile_cols[0][0] + 1
    if tile_h < 3 or tile_w < 3:
        return out

    # The interior has one dominant filler color. Other interior colors are
    # markers whose matching copies define horizontal or vertical segments.
    interior_values = []
    for r0, r1 in tile_rows:
        for c0, c1 in tile_cols:
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    interior_values.append(grid[r][c])
    if not interior_values:
        return out
    filler = Counter(interior_values).most_common(1)[0][0]

    # Group markers by both color and position inside a tile. This preserves
    # distinct symbols that happen to share a color but occupy different cells.
    markers = defaultdict(set)
    for tr, (r0, r1) in enumerate(tile_rows):
        for tc, (c0, c1) in enumerate(tile_cols):
            for r in range(r0 + 1, r1):
                for c in range(c0 + 1, c1):
                    color = grid[r][c]
                    if color != filler:
                        markers[(color, r - r0, c - c0)].add((tr, tc))

    for (color, rel_r, rel_c), points in markers.items():
        by_row = defaultdict(list)
        by_col = defaultdict(list)
        for tr, tc in points:
            by_row[tr].append(tc)
            by_col[tc].append(tr)

        # Fill between the outermost matching markers in each aligned row.
        for tr, cols in by_row.items():
            if len(cols) >= 2:
                for tc in range(min(cols), max(cols) + 1):
                    r0 = tile_rows[tr][0]
                    c0 = tile_cols[tc][0]
                    out[r0 + rel_r][c0 + rel_c] = color

        # Fill between the outermost matching markers in each aligned column.
        for tc, rows in by_col.items():
            if len(rows) >= 2:
                for tr in range(min(rows), max(rows) + 1):
                    r0 = tile_rows[tr][0]
                    c0 = tile_cols[tc][0]
                    out[r0 + rel_r][c0 + rel_c] = color

    return out
