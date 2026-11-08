def solve(grid):
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not points:
        raise ValueError("expected at least one nonzero cell")
    top = min(r for r, _ in points)
    bottom = max(r for r, _ in points)
    left = min(c for _, c in points)
    right = max(c for _, c in points)
    half_h = (bottom - top + 1) // 2
    half_w = (right - left + 1) // 2
    return [
        list(row[left : left + half_w])
        for row in grid[top : top + half_h]
    ]
