def solve(grid):
    scale = len({color for row in grid for color in row})
    return [
        [color for color in row for _ in range(scale)]
        for row in grid
        for _ in range(scale)
    ]
