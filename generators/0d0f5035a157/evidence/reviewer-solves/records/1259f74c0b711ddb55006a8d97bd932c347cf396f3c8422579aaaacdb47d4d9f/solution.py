"""Visible-example solution for the prepared 0d0f5035a157 episode."""


def solve(grid):
    """Stable-compact each row's nonzero values to the left."""
    output = []
    for row in grid:
        values = [value for value in row if value != 0]
        output.append(values + [0] * (len(row) - len(values)))
    return output
