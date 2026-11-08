def solve(grid):
    """Translate the nonzero pattern so its bounding box starts at (0, 0)."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [[0] * w for _ in range(h)]
    pixels = [(r, c, value) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value != 0]
    if not pixels:
        return out
    top = min(r for r, _, _ in pixels)
    left = min(c for _, c, _ in pixels)
    for r, c, value in pixels:
        out[r - top][c - left] = value
    return out
