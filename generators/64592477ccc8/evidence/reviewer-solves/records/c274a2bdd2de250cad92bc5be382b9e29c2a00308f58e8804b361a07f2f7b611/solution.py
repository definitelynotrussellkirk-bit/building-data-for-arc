def solve(grid):
    """Complete the perimeter of each nonzero color's corner-defined rectangle."""
    out = [row[:] for row in grid]
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

        for c in range(left, right + 1):
            out[top][c] = color
            out[bottom][c] = color
        for r in range(top, bottom + 1):
            out[r][left] = color
            out[r][right] = color

    return out
