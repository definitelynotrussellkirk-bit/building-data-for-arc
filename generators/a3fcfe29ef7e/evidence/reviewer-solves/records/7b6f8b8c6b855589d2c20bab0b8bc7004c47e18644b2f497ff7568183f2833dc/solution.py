def solve(grid):
    """Cellwise NOR of the two 3-column panels around the separator."""
    return [
        [3 if row[c] == 0 and row[c + 4] == 0 else 0 for c in range(3)]
        for row in grid
    ]
