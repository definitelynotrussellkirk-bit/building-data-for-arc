"""Place a top-to-bottom reflection above a fresh copy of the input."""


def solve(grid):
    return [list(row) for row in reversed(grid)] + [list(row) for row in grid]
