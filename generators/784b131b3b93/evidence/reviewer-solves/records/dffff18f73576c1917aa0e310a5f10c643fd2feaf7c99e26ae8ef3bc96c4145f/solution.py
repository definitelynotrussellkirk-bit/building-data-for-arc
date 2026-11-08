def solve(grid):
    """Mark cells that are blank in both side-by-side panels."""
    if not grid:
        return []

    width = len(grid[0])
    if width % 2:
        raise ValueError("expected two equal-width panels")
    half = width // 2

    return [
        [5 if row[col] == 0 and row[col + half] == 0 else 0 for col in range(half)]
        for row in grid
    ]
