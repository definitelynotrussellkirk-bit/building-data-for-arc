def solve(grid):
    """Complete isolated diagonal pairs in each original 2 by 2 window."""
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c:c + 2]
            d, e = grid[r + 1][c:c + 2]
            if a != 0 and a == e and b == 0 and d == 0:
                out[r][c + 1] = out[r + 1][c] = a
            elif b != 0 and b == d and a == 0 and e == 0:
                out[r][c] = out[r + 1][c + 1] = b
    return out
