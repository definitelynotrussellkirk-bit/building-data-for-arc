def solve(grid):
    """Arrange the colored shapes in the order shown by the top-row key."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [[0] * w for _ in range(h)]
    if not h or not w:
        return out
    order = []
    for color in grid[0]:
        if color != 0 and color not in order:
            order.append(color)
    left = 0
    for color in order:
        cells = [(r, c) for r in range(1, h) for c in range(w)
                 if grid[r][c] == color]
        if not cells:
            continue
        top = min(r for r, c in cells)
        old_left = min(c for r, c in cells)
        width = max(c for r, c in cells) - old_left + 1
        for r, c in cells:
            out[1 + r - top][left + c - old_left] = color
        left += width + 1
    return out
