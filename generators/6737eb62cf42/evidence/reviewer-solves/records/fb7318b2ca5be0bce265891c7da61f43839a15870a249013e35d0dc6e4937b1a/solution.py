"""Visible-example solution: crop to the tight bounding box of nonzero cells."""


def solve(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return [[0]]
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [list(row[left : right + 1]) for row in grid[top : bottom + 1]]
