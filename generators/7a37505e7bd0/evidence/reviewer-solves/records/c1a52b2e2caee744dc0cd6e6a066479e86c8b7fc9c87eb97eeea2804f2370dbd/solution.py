def solve(grid):
    """Repeat each cell in a square sized by the number of distinct colors."""
    factor = len({color for row in grid for color in row})
    out = []
    for row in grid:
        expanded = [color for color in row for _ in range(factor)]
        out.extend(expanded[:] for _ in range(factor))
    return out
