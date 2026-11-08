def solve(grid):
    """Crop the object and rotate clockwise by the upper-left marker."""
    cells = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row)
             if value != 0 and (r, c) != (0, 0)]
    if not cells:
        return [[0]]
    top = min(r for r, c in cells)
    bottom = max(r for r, c in cells)
    left = min(c for r, c in cells)
    right = max(c for r, c in cells)
    out = [list(row[left:right + 1]) for row in grid[top:bottom + 1]]
    for _ in range(int(grid[0][0]) % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out
