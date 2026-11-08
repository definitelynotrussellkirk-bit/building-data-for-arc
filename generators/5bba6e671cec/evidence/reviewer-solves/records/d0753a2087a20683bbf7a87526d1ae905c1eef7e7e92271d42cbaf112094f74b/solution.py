"""Rotate whole-color regions in clockwise order; frame pixels stay fixed."""
import math


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    fixed = {4, 7}
    points = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color not in fixed:
                points.setdefault(color, []).append((row, col))
    if len(points) < 2:
        return [list(row) for row in grid]

    def angle(color):
        cells = points[color]
        mean_row = sum(r for r, _ in cells) / len(cells)
        mean_col = sum(c for _, c in cells) / len(cells)
        return math.atan2(mean_row - (height - 1) / 2,
                          mean_col - (width - 1) / 2)

    order = sorted(points, key=angle)
    replacements = {color: order[(i - 1) % len(order)]
                    for i, color in enumerate(order)}
    return [[replacements.get(color, color) for color in row] for row in grid]
