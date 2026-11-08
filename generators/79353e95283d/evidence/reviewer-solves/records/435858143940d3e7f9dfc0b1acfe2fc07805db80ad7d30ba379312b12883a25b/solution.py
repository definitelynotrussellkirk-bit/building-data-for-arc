def solve(grid):
    """Intersect the aligned binary panels, emitting 2 for shared foreground."""
    return [
        [2 if row[c] == 1 and row[c + 4] == 1 else 0 for c in range(3)]
        for row in grid
    ]
