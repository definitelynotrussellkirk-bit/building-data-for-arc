def solve(grid):
    """Crop between the gray boundary columns, with one extra row at each end."""
    markers = [(r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 5]
    if not markers:
        return [list(row) for row in grid]
    top = max(0, min(r for r, _ in markers) - 1)
    bottom = min(len(grid), max(r for r, _ in markers) + 2)
    left = min(c for _, c in markers)
    right = max(c for _, c in markers) + 1
    return [list(row[left:right]) for row in grid[top:bottom]]
