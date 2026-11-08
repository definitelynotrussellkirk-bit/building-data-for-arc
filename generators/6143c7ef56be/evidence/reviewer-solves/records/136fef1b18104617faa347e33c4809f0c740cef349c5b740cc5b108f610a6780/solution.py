def solve(grid):
    """Move the four quadrant markers into the four cells of the gray 2x2 block."""
    height = len(grid)
    width = len(grid[0])

    gray = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]
    if len(gray) != 4:
        raise ValueError("expected exactly four gray cells")

    top = min(r for r, _ in gray)
    bottom = max(r for r, _ in gray)
    left = min(c for _, c in gray)
    right = max(c for _, c in gray)
    if bottom != top + 1 or right != left + 1 or set(gray) != {
        (top, left), (top, right), (bottom, left), (bottom, right)
    }:
        raise ValueError("gray cells must form a 2x2 block")

    center_r = (top + bottom) / 2
    center_c = (left + right) / 2
    quadrant_colors = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 8):
                continue
            quadrant = (r < center_r, c < center_c)  # (upper, left)
            if quadrant in quadrant_colors:
                raise ValueError("expected one marker in each quadrant")
            quadrant_colors[quadrant] = value

    expected = {(True, True), (True, False), (False, True), (False, False)}
    if set(quadrant_colors) != expected:
        raise ValueError("markers must occupy all four quadrants")

    result = [[0] * width for _ in range(height)]
    result[top][left] = quadrant_colors[(True, True)]
    result[top][right] = quadrant_colors[(True, False)]
    result[bottom][left] = quadrant_colors[(False, True)]
    result[bottom][right] = quadrant_colors[(False, False)]
    return result
