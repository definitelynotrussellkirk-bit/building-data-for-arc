def solve(grid):
    """Append a vertical reflection of the input below the original grid."""
    rows = [list(row) for row in grid]
    return rows + [row.copy() for row in reversed(rows)]
