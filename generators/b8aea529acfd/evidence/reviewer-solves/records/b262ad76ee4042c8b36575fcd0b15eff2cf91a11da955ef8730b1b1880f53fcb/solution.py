def solve(grid):
    """Crop all nonzero content and reverse each cropped row."""
    cells = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value != 0]
    if not cells:
        raise ValueError("The visible examples require nonempty foreground")
    top = min(r for r, c in cells)
    bottom = max(r for r, c in cells)
    left = min(c for r, c in cells)
    right = max(c for r, c in cells)
    return [list(reversed(row[left:right + 1])) for row in grid[top:bottom + 1]]
