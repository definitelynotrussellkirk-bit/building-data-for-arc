"""Solve the displayed examples by outlining the occupied bounding rectangle."""


def solve(grid):
    result = [list(row) for row in grid]
    occupied = [(r, c) for r, row in enumerate(grid)
                for c, value in enumerate(row) if value != 0]
    if not occupied:
        return result
    top = min(r for r, _ in occupied)
    bottom = max(r for r, _ in occupied)
    left = min(c for _, c in occupied)
    right = max(c for _, c in occupied)
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            if (r in (top, bottom) or c in (left, right)) and grid[r][c] == 0:
                result[r][c] = 8
    return result
