"""Visible-example solution for reviewer episode 3020cc038f3f."""


def _normalized_cells(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        return set()
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}


def solve(grid):
    first = _normalized_cells(grid, 1)
    second = _normalized_cells(grid, 2)
    ctrl = grid[0][0]
    if ctrl == 3:
        result = first | second
    elif ctrl == 4:
        result = first ^ second
    elif ctrl == 5:
        result = first & second
    else:
        result = set()

    if not result:
        return [[0]]
    height = max(
        max((r for r, _ in first), default=-1),
        max((r for r, _ in second), default=-1),
    ) + 1
    width = max(
        max((c for _, c in first), default=-1),
        max((c for _, c in second), default=-1),
    ) + 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in result:
        output[r][c] = 8
    return output
