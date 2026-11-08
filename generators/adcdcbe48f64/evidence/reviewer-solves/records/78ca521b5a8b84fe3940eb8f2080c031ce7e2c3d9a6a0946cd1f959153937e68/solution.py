def solve(grid):
    return [
        list(row) + list(reversed(row)) + list(row) + list(reversed(row)) + list(row)
        for row in grid
    ]
