"""Visible-example solution: fill each nonzero color's bounding rectangle."""


def solve(grid):
    output = [row[:] for row in grid]
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append((r, c))
    for color, cells in by_color.items():
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                output[r][c] = color
    return output
