def solve(grid):
    """Keep the color-5 mask, recolored with the other input color."""
    other = next(value for row in grid for value in row if value != 5)
    return [[other if value == 5 else 0 for value in row] for row in grid]
