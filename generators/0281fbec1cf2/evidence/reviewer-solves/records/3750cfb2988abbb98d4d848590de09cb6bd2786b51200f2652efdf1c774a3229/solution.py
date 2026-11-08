def solve(grid):
    """Extend a solid red rectangle outward, with colored markers blocking rays.

    Each row occupied by the red (2) rectangle can extend independently to the
    left and right border.  A nonzero marker anywhere on one side blocks that
    whole side-ray.  The same rule applies independently above and below for
    every rectangle column.  Existing cells, including blockers, are preserved.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    if not red:
        return out

    top = min(r for r, _ in red)
    bottom = max(r for r, _ in red)
    left = min(c for _, c in red)
    right = max(c for _, c in red)

    # Horizontal rays from each rectangle row.
    for r in range(top, bottom + 1):
        if all(grid[r][c] == 0 for c in range(left)):
            for c in range(left):
                out[r][c] = 2
        if all(grid[r][c] == 0 for c in range(right + 1, width)):
            for c in range(right + 1, width):
                out[r][c] = 2

    # Vertical rays from each rectangle column.
    for c in range(left, right + 1):
        if all(grid[r][c] == 0 for r in range(top)):
            for r in range(top):
                out[r][c] = 2
        if all(grid[r][c] == 0 for r in range(bottom + 1, height)):
            for r in range(bottom + 1, height):
                out[r][c] = 2

    return out
