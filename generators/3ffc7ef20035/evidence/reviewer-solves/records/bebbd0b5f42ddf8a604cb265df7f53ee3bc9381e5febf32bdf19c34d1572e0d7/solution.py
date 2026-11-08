def solve(grid):
    """Complete the bounding rectangle of blue cells in cyan."""
    output = [list(row) for row in grid]
    blue = [(r, c) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value == 1]
    if not blue:
        return output
    top = min(r for r, _ in blue)
    bottom = max(r for r, _ in blue)
    left = min(c for _, c in blue)
    right = max(c for _, c in blue)
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            output[r][c] = 8
    return output
