"""Infer row colors from the leftmost nonzero cell; preserve empty cells."""


def solve(grid):
    result = []
    for row in grid:
        color = next((value for value in row if value != 0), 0)
        result.append([color if value != 0 else 0 for value in row])
    return result
