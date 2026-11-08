"""Infer the alternating expansion shown by the visible examples only."""


def solve(grid):
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    result = [[0 for _ in range(width)] for _ in range(height)]
    for column, color in enumerate(grid[0]):
        if color == 0:
            continue
        for row in range(height):
            columns = (column,) if row % 2 == 0 else (column - 1, column + 1)
            for target in columns:
                if 0 <= target < width:
                    result[row][target] = color
    return result
