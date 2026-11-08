def solve(grid):
    """Mirror all non-background, non-axis cells across the complete 5-axis."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [row[:] for row in grid]

    axis_row = next((r for r, row in enumerate(grid) if all(v == 5 for v in row)), None)
    axis_col = None
    if axis_row is None and h:
        axis_col = next(
            (c for c in range(w) if all(grid[r][c] == 5 for r in range(h))),
            None,
        )

    if axis_row is not None:
        for r in range(h):
            for c in range(w):
                value = grid[r][c]
                if value in (0, 5):
                    continue
                rr = 2 * axis_row - r
                if 0 <= rr < h:
                    out[rr][c] = value
    elif axis_col is not None:
        for r in range(h):
            for c in range(w):
                value = grid[r][c]
                if value in (0, 5):
                    continue
                cc = 2 * axis_col - c
                if 0 <= cc < w:
                    out[r][cc] = value

    return out
