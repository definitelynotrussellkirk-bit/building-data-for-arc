def solve(grid):
    """Sort the separator-delimited tiles by their number of color-1 cells.

    Tiles are placed in ascending order left-to-right, starting on the
    bottom tile row and proceeding upward. Separator rows and columns are
    preserved.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or any(len(row) != width for row in grid):
        raise ValueError("grid must be a non-empty rectangle")

    separator_rows = [r for r, row in enumerate(grid) if all(cell == 0 for cell in row)]
    separator_cols = [c for c in range(width) if all(grid[r][c] == 0 for r in range(height))]

    def spans(size, separators):
        cuts = [-1, *separators, size]
        return [(cuts[i] + 1, cuts[i + 1]) for i in range(len(cuts) - 1) if cuts[i] + 1 < cuts[i + 1]]

    row_spans = spans(height, separator_rows)
    col_spans = spans(width, separator_cols)
    if not row_spans or not col_spans:
        return [row[:] for row in grid]

    shape = (row_spans[0][1] - row_spans[0][0], col_spans[0][1] - col_spans[0][0])
    tiles = []
    for r0, r1 in row_spans:
        for c0, c1 in col_spans:
            if (r1 - r0, c1 - c0) != shape:
                raise ValueError("all separator-delimited tiles must have the same shape")
            tile = [row[c0:c1] for row in grid[r0:r1]]
            tiles.append(tile)

    tiles.sort(key=lambda tile: sum(cell == 1 for row in tile for cell in row))

    result = [row[:] for row in grid]
    destination_spans = [
        (row_span, col_span)
        for row_span in reversed(row_spans)
        for col_span in col_spans
    ]
    for tile, ((r0, r1), (c0, c1)) in zip(tiles, destination_spans):
        for dr, row in enumerate(tile):
            result[r0 + dr][c0:c1] = row
    return result
