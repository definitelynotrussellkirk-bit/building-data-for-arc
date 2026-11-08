def solve(grid):
    """Mirror yellow marks within the visible blue rectangle."""
    out = [row[:] for row in grid]
    blue = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 1]
    if not blue:
        return out
    top = min(r for r, _ in blue)
    bottom = max(r for r, _ in blue)
    left = min(c for _, c in blue)
    right = max(c for _, c in blue)
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if grid[r][c] == 4:
                reflected = left + right - c
                if grid[r][reflected] == 0:
                    out[r][reflected] = 7
    return out
