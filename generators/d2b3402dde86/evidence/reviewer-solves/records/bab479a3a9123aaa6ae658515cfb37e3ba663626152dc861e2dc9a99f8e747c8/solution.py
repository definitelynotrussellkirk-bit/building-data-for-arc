def solve(grid):
    """Return the upper-left half-quadrant of the nonzero bounding box."""
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return []

    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)

    out_h = (bottom - top + 1) // 2
    out_w = (right - left + 1) // 2
    return [row[left : left + out_w] for row in grid[top : top + out_h]]
