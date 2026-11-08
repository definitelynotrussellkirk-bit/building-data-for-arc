def solve(grid):
    """Paint intersections of top-border 1s and left-border 2s with 3."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    selected_columns = [c for c in range(width) if grid[0][c] == 1]
    selected_rows = [r for r in range(height) if grid[r][0] == 2]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r in selected_rows:
        for c in selected_columns:
            output[r][c] = 3
    return output
