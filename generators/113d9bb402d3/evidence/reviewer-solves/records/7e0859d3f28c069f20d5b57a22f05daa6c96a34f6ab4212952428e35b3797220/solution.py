def solve(grid):
    """Recolor blue cells enclosed by the gray cells' bounding box."""
    result = [row[:] for row in grid]
    gray = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not gray:
        return result

    min_r = min(r for r, _ in gray)
    max_r = max(r for r, _ in gray)
    min_c = min(c for _, c in gray)
    max_c = max(c for _, c in gray)

    for r in range(min_r, max_r + 1):
        for c in range(min_c, max_c + 1):
            if result[r][c] == 1:
                result[r][c] = 3
    return result
