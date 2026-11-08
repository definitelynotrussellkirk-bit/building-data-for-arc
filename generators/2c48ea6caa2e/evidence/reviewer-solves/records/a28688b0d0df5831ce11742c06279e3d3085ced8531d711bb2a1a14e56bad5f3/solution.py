def solve(grid):
    """Complete the visible blue frame and supported vertical dividers in red."""
    out = [list(row) for row in grid]
    blue = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    if not blue:
        return out
    top = min(r for r, _ in blue)
    bottom = max(r for r, _ in blue)
    left = min(c for _, c in blue)
    right = max(c for _, c in blue)
    columns = {left, right}
    for c in range(left + 1, right):
        if sum(grid[r][c] == 1 for r in range(top, bottom + 1)) >= 3:
            columns.add(c)
    for c in range(left, right + 1):
        for r in (top, bottom):
            if out[r][c] == 0:
                out[r][c] = 2
    for c in columns:
        for r in range(top, bottom + 1):
            if out[r][c] == 0:
                out[r][c] = 2
    return out
