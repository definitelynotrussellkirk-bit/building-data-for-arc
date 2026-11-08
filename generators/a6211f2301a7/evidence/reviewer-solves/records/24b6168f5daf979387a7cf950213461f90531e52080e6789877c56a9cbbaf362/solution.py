def solve(grid):
    """Crop the nonzero pattern and rotate it 90 degrees clockwise."""
    cells = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value != 0]
    if not cells:
        return []
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    crop = [row[left:right + 1] for row in grid[top:bottom + 1]]
    return [list(row) for row in zip(*crop[::-1])]
