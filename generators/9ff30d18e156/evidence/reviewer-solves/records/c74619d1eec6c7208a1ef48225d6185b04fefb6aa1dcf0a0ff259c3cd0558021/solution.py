"""Visible-only solution for blind task 9ff30d18e156."""


def solve(grid):
    """Fill each repeated nonzero row color between its extreme occurrences."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        positions = {}
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append(c)
        for value, cols in positions.items():
            if len(cols) >= 2:
                for c in range(min(cols), max(cols) + 1):
                    out[r][c] = value
    return out
