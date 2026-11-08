def solve(grid):
    """Complete reflection inside the visible rectangular outline."""
    frames = []
    for color in range(1, 10):
        cells = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == color}
        if not cells:
            continue
        top = min(r for r, c in cells)
        bottom = max(r for r, c in cells)
        left = min(c for r, c in cells)
        right = max(c for r, c in cells)
        if bottom - top < 2 or right - left < 2:
            continue
        outline = {(r, c) for r in range(top, bottom + 1)
                   for c in range(left, right + 1)
                   if r in (top, bottom) or c in (left, right)}
        if cells == outline:
            frames.append((len(cells), top, bottom, left, right, color))
    output = [list(row) for row in grid]
    if not frames:
        return output
    _, top, bottom, left, right, frame_color = max(frames)
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            value = grid[r][c]
            if value not in (0, frame_color):
                output[r][left + right - c] = value
    return output
