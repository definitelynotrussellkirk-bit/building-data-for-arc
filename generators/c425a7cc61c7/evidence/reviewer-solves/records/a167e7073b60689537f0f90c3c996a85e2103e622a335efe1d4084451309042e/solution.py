def solve(grid):
    """Extract the object whose color is named at (0, 0), then rotate it clockwise."""
    target = grid[0][0]
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == target and (r, c) != (0, 0)
    ]
    if not cells:
        raise ValueError("marker color has no object")

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    cropped = [
        [target if grid[r][c] == target else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]
    return [list(row) for row in zip(*cropped[::-1])]
