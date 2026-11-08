def solve(grid):
    """Fill the frame's interior by Manhattan-nearest seed, then lowest color."""
    result = [row[:] for row in grid]
    frame = [(r, c) for r, row in enumerate(grid)
             for c, color in enumerate(row) if color == 7]
    if not frame:
        return result

    top = min(r for r, _ in frame)
    bottom = max(r for r, _ in frame)
    left = min(c for _, c in frame)
    right = max(c for _, c in frame)
    seeds = [(r, c, grid[r][c])
             for r in range(top + 1, bottom)
             for c in range(left + 1, right)
             if grid[r][c] not in (0, 7)]
    if not seeds:
        return result

    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if grid[r][c] == 0:
                result[r][c] = min(
                    (abs(r - sr) + abs(c - sc), color)
                    for sr, sc, color in seeds
                )[1]
    return result
