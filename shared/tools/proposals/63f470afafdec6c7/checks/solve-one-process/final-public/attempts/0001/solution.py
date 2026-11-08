def solve(grid):
    height = len(grid)
    width = len(grid[0])
    rows = [r for r in range(height) if all(grid[r][c] != 0 for c in range(width))]
    columns = [c for c in range(width) if all(grid[r][c] != 0 for r in range(height))]
    if len(rows) != 1 or len(columns) != 1:
        raise ValueError("Expected one crossing row and column")
    row, col = rows[0], columns[0]
    output = [values[:] for values in grid]
    for rr in range(max(0, row - 1), min(height, row + 2)):
        for cc in range(max(0, col - 1), min(width, col + 2)):
            if (rr, cc) != (row, col):
                output[rr][cc] = 4
    return output
