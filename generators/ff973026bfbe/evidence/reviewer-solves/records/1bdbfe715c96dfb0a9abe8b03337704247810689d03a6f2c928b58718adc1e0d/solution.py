def solve(grid):
    """Paint active row/column intersections green (colour 3)."""
    output = [row[:] for row in grid]
    active_rows = [r for r, row in enumerate(grid) if 1 in row]
    active_cols = [c for c, value in enumerate(grid[0]) if value == 2]
    for r in active_rows:
        for c in active_cols:
            output[r][c] = 3
    return output
