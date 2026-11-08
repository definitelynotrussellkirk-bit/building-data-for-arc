from collections import Counter


def _spans(active):
    """Return inclusive-exclusive runs whose corresponding flag is true."""
    runs = []
    start = None
    for i, flag in enumerate(active + [False]):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            runs.append((start, i))
            start = None
    return runs


def solve(grid):
    """Copy the marked exemplar tile into every tile containing a zero defect."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    # Entirely zero rows/columns are the dividers between equal-sized tiles.
    row_spans = _spans([any(value != 0 for value in row) for row in grid])
    col_spans = _spans([
        any(grid[r][c] != 0 for r in range(height))
        for c in range(width)
    ])

    nonzero = [value for row in grid for value in row if value != 0]
    base = Counter(nonzero).most_common(1)[0][0]

    template = None
    for r0, r1 in row_spans:
        for c0, c1 in col_spans:
            tile = [row[c0:c1] for row in grid[r0:r1]]
            if any(value not in (0, base) for row in tile for value in row):
                template = tile
                break
        if template is not None:
            break

    if template is None:
        return out

    for r0, r1 in row_spans:
        for c0, c1 in col_spans:
            tile = [row[c0:c1] for row in grid[r0:r1]]
            if any(value == 0 for row in tile for value in row):
                for tr, row in enumerate(template):
                    out[r0 + tr][c0:c1] = row[:]

    return out
