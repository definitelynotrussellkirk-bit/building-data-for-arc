def solve(grid):
    """Crop the payload; marker 6 requests reversal of its row order."""
    marker = grid[0][0]
    occupied = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    ]
    if not occupied:
        return []

    top = min(r for r, c in occupied)
    bottom = max(r for r, c in occupied)
    left = min(c for r, c in occupied)
    right = max(c for r, c in occupied)
    result = [list(row[left:right + 1]) for row in grid[top:bottom + 1]]

    if marker == 6:
        result.reverse()
    return result
