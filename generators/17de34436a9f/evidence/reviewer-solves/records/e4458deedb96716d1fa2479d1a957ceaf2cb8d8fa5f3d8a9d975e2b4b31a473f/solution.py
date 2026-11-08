def solve(grid):
    """Crop the colored object, then rotate by the corner marker."""
    height, width = len(grid), len(grid[0])
    corners = [(0, 0), (0, width - 1), (height - 1, width - 1), (height - 1, 0)]
    markers = [i for i, (r, c) in enumerate(corners) if grid[r][c] == 9]
    if len(markers) != 1:
        raise ValueError("Expected one corner marker of color 9")
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 9)]
    if not cells:
        raise ValueError("Expected a colored object")
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    cropped = [[grid[r][c] if grid[r][c] != 9 else 0
                for c in range(left, right + 1)] for r in range(top, bottom + 1)]
    for _ in range(markers[0]):
        cropped = [list(row) for row in zip(*cropped[::-1])]
    return cropped
