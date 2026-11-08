def solve(grid):
    height, width = len(grid), len(grid[0])
    result = [[0] * width for _ in range(height)]
    for column in range(width):
        destination = height - 1
        for row in range(height - 1, -1, -1):
            value = grid[row][column]
            if value != 0:
                result[destination][column] = value
                destination -= 1
    return result
