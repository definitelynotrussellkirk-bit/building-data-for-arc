def solve(grid):
    """Extend cyan rays from each red source until a gray blocker or edge."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [list(row) for row in grid]

    for row in range(height):
        for column in range(width):
            if grid[row][column] != 2:
                continue
            output[row][column] = 8
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                r, c = row + dr, column + dc
                while 0 <= r < height and 0 <= c < width:
                    if grid[r][c] == 5:
                        break
                    output[r][c] = 8
                    r += dr
                    c += dc

    return output
