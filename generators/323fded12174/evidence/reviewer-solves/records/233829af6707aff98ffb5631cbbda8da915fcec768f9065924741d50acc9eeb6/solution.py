def solve(grid):
    """Stable-sort rows by descending number of nonzero cells."""
    return [list(row) for row in sorted(grid, key=lambda row: sum(v != 0 for v in row), reverse=True)]
