"""Visible-example solution for the generated ARC lesson."""


def solve(grid):
    key = next((value for row in grid for value in row if value != 0), None)
    if key is None:
        return [list(row) for row in grid]
    return [[value if value == key else 0 for value in row] for row in grid]
