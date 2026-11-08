def solve(grid):
    factor = max(1, len({value for row in grid for value in row if value != 0}))
    return [
        [value for value in row for _ in range(factor)]
        for row in grid
        for _ in range(factor)
    ]
