"""Visible-example solve for task 3bb94038f4e2."""


def solve(grid):
    """Fill the zero in every horizontal 1-0-1 triple with color 1."""
    source = [list(row) for row in grid]
    out = [row[:] for row in source]
    for r, row in enumerate(source):
        for c in range(1, len(row) - 1):
            if row[c - 1:c + 2] == [1, 0, 1]:
                out[r][c] = 1
    return out
