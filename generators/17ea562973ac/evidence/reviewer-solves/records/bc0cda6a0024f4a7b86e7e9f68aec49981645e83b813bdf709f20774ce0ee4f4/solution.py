"""Inferred only from the three visible demonstrations."""


def solve(grid):
    out = [[0 for _ in row] for row in grid]
    points = [(r, c, value) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value != 0]
    if not points:
        return out
    top = min(r for r, _, _ in points)
    bottom = max(r for r, _, _ in points)
    left = min(c for _, c, _ in points)
    right = max(c for _, c, _ in points)
    color = points[0][2]
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            if r in (top, bottom) or c in (left, right):
                out[r][c] = color
    return out
