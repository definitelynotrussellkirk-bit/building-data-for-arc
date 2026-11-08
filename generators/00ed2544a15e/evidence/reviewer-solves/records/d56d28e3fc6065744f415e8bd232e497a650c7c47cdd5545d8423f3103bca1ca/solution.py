def solve(grid):
    """Join red endpoints through entirely empty horizontal/vertical gaps."""
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(height):
        endpoints = [col for col in range(width) if grid[row][col] == 2]
        for left, right in zip(endpoints, endpoints[1:]):
            if all(grid[row][col] == 0 for col in range(left + 1, right)):
                for col in range(left + 1, right):
                    out[row][col] = 8
    for col in range(width):
        endpoints = [row for row in range(height) if grid[row][col] == 2]
        for top, bottom in zip(endpoints, endpoints[1:]):
            if all(grid[row][col] == 0 for row in range(top + 1, bottom)):
                for row in range(top + 1, bottom):
                    out[row][col] = 8
    return out
