def solve(grid):
    """Complete the missing corner(s) of each color's bounding rectangle."""
    result = [row[:] for row in grid]
    positions = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((r, c))

    for color, cells in positions.items():
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        for r, c in ((top, left), (top, right), (bottom, left), (bottom, right)):
            if result[r][c] == 0:
                result[r][c] = color
    return result
