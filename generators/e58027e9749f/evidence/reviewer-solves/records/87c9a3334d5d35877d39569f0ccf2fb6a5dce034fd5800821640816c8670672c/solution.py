def solve(grid):
    """Keep each colored cell and add its main-diagonal reflection."""
    n = len(grid)
    if not n or any(len(row) != n for row in grid):
        raise ValueError("The visible task uses nonempty square grids")
    result = [list(row) for row in grid]
    for row in range(n):
        for column in range(n):
            if grid[row][column] != 0:
                result[column][row] = grid[row][column]
    return result
