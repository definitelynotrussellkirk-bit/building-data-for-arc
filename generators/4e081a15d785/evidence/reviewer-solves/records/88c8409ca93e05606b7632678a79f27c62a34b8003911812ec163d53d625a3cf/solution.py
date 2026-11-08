def solve(grid):
    """Keep each changed full row and each column boundary seen in any row."""
    row_indices = [r for r in range(len(grid))
                   if r == 0 or grid[r] != grid[r - 1]]
    column_indices = [c for c in range(len(grid[0]))
                      if c == 0 or any(grid[r][c] != grid[r][c - 1]
                                       for r in row_indices)]
    return [[grid[r][c] for c in column_indices] for r in row_indices]
