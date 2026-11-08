def solve(grid):
    """Recolor the union of complete red 2x2 squares to green."""
    result = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    # Inspect the original grid so overlapping squares remain detectable.
    for row in range(height - 1):
        for col in range(width - 1):
            if all(
                grid[row + dr][col + dc] == 2
                for dr in (0, 1)
                for dc in (0, 1)
            ):
                for dr in (0, 1):
                    for dc in (0, 1):
                        result[row + dr][col + dc] = 3
    return result
