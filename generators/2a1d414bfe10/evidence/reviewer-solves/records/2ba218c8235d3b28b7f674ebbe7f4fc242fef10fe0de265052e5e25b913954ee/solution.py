from collections import Counter


def solve(grid):
    """Align each colored shape, retain double coverage, and crop it."""
    shapes = {}
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color != 0:
                shapes.setdefault(color, []).append((row, column))

    coverage = Counter()
    for points in shapes.values():
        top = min(row for row, column in points)
        left = min(column for row, column in points)
        coverage.update((row - top, column - left) for row, column in points)

    marked = {point for point, count in coverage.items() if count == 2}
    if not marked:
        return [[0]]

    top = min(row for row, column in marked)
    bottom = max(row for row, column in marked)
    left = min(column for row, column in marked)
    right = max(column for row, column in marked)
    return [
        [8 if (row, column) in marked else 0 for column in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]
