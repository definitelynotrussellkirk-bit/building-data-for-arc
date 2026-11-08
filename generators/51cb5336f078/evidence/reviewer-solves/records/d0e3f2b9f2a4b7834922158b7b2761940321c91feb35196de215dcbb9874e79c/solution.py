def solve(grid):
    """Replace the nonzero object by its tight rectangular frame."""
    height, width = len(grid), len(grid[0])
    occupied = [(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0]
    output = [[0] * width for _ in range(height)]
    if not occupied:
        return output
    top = min(r for r, c in occupied)
    bottom = max(r for r, c in occupied)
    left = min(c for r, c in occupied)
    right = max(c for r, c in occupied)
    row, col = occupied[0]
    color = grid[row][col]
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            if r == top or r == bottom or c == left or c == right:
                output[r][c] = color
    return output
