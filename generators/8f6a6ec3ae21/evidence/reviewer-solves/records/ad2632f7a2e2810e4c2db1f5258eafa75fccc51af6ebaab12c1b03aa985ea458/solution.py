def solve(grid):
    """Render the Cartesian product encoded by the top and left borders.

    Color 2 on the top border selects columns. Color 1 on the left border
    selects rows. Every selected row/column intersection becomes color 8;
    all other cells, including both marker borders, become background.
    """
    height = len(grid)
    if height == 0:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    selected_rows = [r for r in range(1, height) if grid[r][0] == 1]
    selected_cols = [c for c in range(1, width) if grid[0][c] == 2]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for r in selected_rows:
        for c in selected_cols:
            output[r][c] = 8
    return output
