from collections import Counter


def _spans(length, separators):
    """Return half-open runs between one-cell separator lines."""
    spans = []
    start = 0
    for stop in separators + [length]:
        if start < stop:
            spans.append((start, stop))
        start = stop + 1
    return spans


def solve(grid):
    """Restore damaged tiles and stamp the intact motif into each damaged tile."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separator_rows = [r for r, row in enumerate(grid) if all(value == 0 for value in row)]
    separator_cols = [
        c for c in range(width) if all(grid[r][c] == 0 for r in range(height))
    ]
    row_spans = _spans(height, separator_rows)
    col_spans = _spans(width, separator_cols)

    tile_values = [
        grid[r][c]
        for r0, r1 in row_spans
        for c0, c1 in col_spans
        for r in range(r0, r1)
        for c in range(c0, c1)
        if grid[r][c] != 0
    ]
    if not tile_values:
        return [row[:] for row in grid]
    background = Counter(tile_values).most_common(1)[0][0]

    motif = None
    motif_shape = None
    flagged = set()

    for tile_r, (r0, r1) in enumerate(row_spans):
        for tile_c, (c0, c1) in enumerate(col_spans):
            tile = [row[c0:c1] for row in grid[r0:r1]]
            if any(value == 0 for row in tile for value in row):
                flagged.add((tile_r, tile_c))
            if any(value not in (0, background) for row in tile for value in row):
                if motif is not None:
                    raise ValueError("expected exactly one motif tile")
                motif = tile
                motif_shape = (r1 - r0, c1 - c0)
                flagged.add((tile_r, tile_c))

    if motif is None:
        return [row[:] for row in grid]

    output = [row[:] for row in grid]
    for tile_r, (r0, r1) in enumerate(row_spans):
        for tile_c, (c0, c1) in enumerate(col_spans):
            shape = (r1 - r0, c1 - c0)
            if shape != motif_shape:
                raise ValueError("all tiles must have the motif tile's dimensions")

            for r in range(r0, r1):
                for c in range(c0, c1):
                    output[r][c] = background

            if (tile_r, tile_c) in flagged:
                for local_r, row in enumerate(motif):
                    for local_c, value in enumerate(row):
                        if value != background:
                            output[r0 + local_r][c0 + local_c] = value

    return output
