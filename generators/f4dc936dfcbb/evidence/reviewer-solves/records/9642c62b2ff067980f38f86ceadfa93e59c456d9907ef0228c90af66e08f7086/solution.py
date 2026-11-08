def solve(grid):
    """Mark row-2-span/column-3-span intersections satisfying both spans."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [[0 for _ in range(w)] for _ in range(h)]

    row_spans = []
    for r, row in enumerate(grid):
        columns = [c for c, value in enumerate(row) if value == 2]
        if len(columns) >= 2:
            row_spans.append((r, min(columns), max(columns)))

    col_spans = []
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] == 3]
        if len(rows) >= 2:
            col_spans.append((c, min(rows), max(rows)))

    for r, c0, c1 in row_spans:
        for c, r0, r1 in col_spans:
            if c0 <= c <= c1 and r0 <= r <= r1:
                out[r][c] = 8
    return out
