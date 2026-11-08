def solve(grid):
    """Keep each colored cell and add its reflection across the main diagonal."""
    n = len(grid)
    if any(len(row) != n for row in grid):
        raise ValueError("The visible task uses square grids")
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                out[c][r] = color
    return out
