def solve(grid):
    """Copy the complete top row down every row of the same-size output."""
    if not grid or not grid[0]:
        return []
    top = list(grid[0])
    return [top[:] for _ in range(len(grid))]
