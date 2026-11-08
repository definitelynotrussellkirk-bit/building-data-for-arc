def solve(grid):
    height, width = len(grid), len(grid[0])
    crossing_row = next(r for r in range(height) if all(grid[r]))
    crossing_col = next(c for c in range(width) if all(grid[r][c] for r in range(height)))
    result = [list(row) for row in grid]
    for r in range(max(0, crossing_row - 1), min(height, crossing_row + 2)):
        for c in range(max(0, crossing_col - 1), min(width, crossing_col + 2)):
            if r != crossing_row or c != crossing_col:
                result[r][c] = 4
    return result
