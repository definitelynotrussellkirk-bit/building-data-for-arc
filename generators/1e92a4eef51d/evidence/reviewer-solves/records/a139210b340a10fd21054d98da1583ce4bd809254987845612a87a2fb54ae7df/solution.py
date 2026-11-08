"""Visible-example solution for the exposed post-repair episode."""


def solve(grid):
    key = grid[0][0]
    body = [row[:] for row in grid]
    body[0][0] = 0
    cells = [
        (r, c)
        for r, row in enumerate(body)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    crop = [row[c0 : c1 + 1] for row in body[r0 : r1 + 1]]
    if key == 1:
        return [row[::-1] for row in crop]
    if key == 2:
        return crop[::-1]
    return crop
