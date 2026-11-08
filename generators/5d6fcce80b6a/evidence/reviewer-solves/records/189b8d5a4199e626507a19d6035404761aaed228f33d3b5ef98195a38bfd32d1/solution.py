def solve(grid):
    """Double the canvas, copy on the block diagonal, and mark separator rows."""
    h = len(grid)
    w = len(grid[0])
    out = [[0 for _ in range(2 * w)] for _ in range(2 * h)]

    nonempty = [any(value != 0 for value in row) for row in grid]
    last_nonempty = max(index for index, present in enumerate(nonempty) if present)

    for r in range(h):
        if not nonempty[r] and r <= last_nonempty:
            out[r] = [3] * (2 * w)
            out[r + h] = [3] * (2 * w)
            continue
        for c, value in enumerate(grid[r]):
            out[r][c] = value
            out[r + h][c + w] = value
    return out
