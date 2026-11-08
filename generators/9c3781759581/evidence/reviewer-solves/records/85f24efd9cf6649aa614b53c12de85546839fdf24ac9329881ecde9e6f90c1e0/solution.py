def solve(grid):
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if not markers:
        raise ValueError("the visible rule requires at least one color-9 marker")
    top = min(r for r, _ in markers)
    bottom = max(r for r, _ in markers)
    left = min(c for _, c in markers)
    right = max(c for _, c in markers)
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]
