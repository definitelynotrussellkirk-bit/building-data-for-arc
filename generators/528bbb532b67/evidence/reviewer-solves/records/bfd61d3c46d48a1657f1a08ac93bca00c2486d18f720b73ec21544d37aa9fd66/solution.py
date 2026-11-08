"""Visible-example hypothesis: complete horizontal symmetry inside the blue frame."""


def solve(grid):
    out = [list(row) for row in grid]
    blue = [(r, c) for r, row in enumerate(grid)
            for c, color in enumerate(row) if color == 8]
    if not blue:
        return out
    top = min(r for r, _ in blue)
    bottom = max(r for r, _ in blue)
    left = min(c for _, c in blue)
    right = max(c for _, c in blue)
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            color = grid[r][c]
            reflected = left + right - c
            if color not in (0, 8) and out[r][reflected] == 0:
                out[r][reflected] = color
    return out
