def solve(grid):
    """Mark crossings reached by both an unblocked right/down ray."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    horizontal = [[False] * width for _ in range(height)]
    vertical = [[False] * width for _ in range(height)]

    for row in range(height):
        launchers = [col for col, value in enumerate(grid[row]) if value == 1]
        for start_col in launchers:
            for col in range(start_col + 1, width):
                if grid[row][col] == 5:
                    break
                horizontal[row][col] = True

    for col in range(width):
        launchers = [row for row in range(height) if grid[row][col] == 2]
        for start_row in launchers:
            for row in range(start_row + 1, height):
                if grid[row][col] == 5:
                    break
                vertical[row][col] = True

    return [
        [6 if horizontal[row][col] and vertical[row][col] else 0 for col in range(width)]
        for row in range(height)
    ]
