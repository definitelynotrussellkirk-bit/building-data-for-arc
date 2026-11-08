def solve(grid):
    """Continue the shortest repeating row pattern and recolor blue to red."""
    height = len(grid)
    if height == 0:
        return []

    period = next(
        candidate
        for candidate in range(1, height + 1)
        if all(grid[row] == grid[row % candidate] for row in range(height))
    )
    return [
        [2 if color == 1 else color for color in grid[row % period]]
        for row in range(height * 3 // 2)
    ]
