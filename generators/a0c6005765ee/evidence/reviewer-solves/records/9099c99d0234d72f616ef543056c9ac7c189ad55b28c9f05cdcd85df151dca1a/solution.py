def solve(grid):
    """Paint green interior rays aligned with orange frame-side markers."""
    out = [list(row) for row in grid]
    frame = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value == 5]
    if not frame:
        return out
    top = min(r for r, _ in frame)
    bottom = max(r for r, _ in frame)
    left = min(c for _, c in frame)
    right = max(c for _, c in frame)
    height, width = len(grid), len(grid[0])
    rows = {r for r in range(top + 1, bottom)
            if (left > 0 and grid[r][left - 1] == 7)
            or (right + 1 < width and grid[r][right + 1] == 7)}
    cols = {c for c in range(left + 1, right)
            if (top > 0 and grid[top - 1][c] == 7)
            or (bottom + 1 < height and grid[bottom + 1][c] == 7)}
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if r in rows or c in cols:
                out[r][c] = 3
    return out
