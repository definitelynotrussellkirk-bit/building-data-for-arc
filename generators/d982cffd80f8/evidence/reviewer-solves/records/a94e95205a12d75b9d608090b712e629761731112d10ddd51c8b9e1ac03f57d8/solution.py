def solve(grid):
    output = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    for row in range(1, height - 1):
        for column in range(1, width - 1):
            if grid[row][column] != 0:
                continue
            border = [
                grid[row + dr][column + dc]
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if (dr, dc) != (0, 0)
            ]
            if border[0] != 0 and all(color == border[0] for color in border):
                output[row][column] = border[0]
    return output
