def solve(grid):
    """Apply the endpoint-marked line transformation seen in the demonstrations."""
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    selected_rows = {r for r in range(height) if grid[r][0] == grid[r][-1] == 4}
    selected_columns = {c for c in range(width) if grid[0][c] == grid[-1][c] == 4}
    substitutions = {0: 8, 8: 0, 6: 7, 7: 6}
    return [[substitutions.get(value, value)
             if r in selected_rows or c in selected_columns else value
             for c, value in enumerate(row)]
            for r, row in enumerate(grid)]
