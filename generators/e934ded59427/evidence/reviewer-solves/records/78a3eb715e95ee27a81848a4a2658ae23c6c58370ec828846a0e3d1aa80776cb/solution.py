def solve(grid):
    """Complete each pair of equal-colored corner markers into a rectangle outline."""
    out = [row[:] for row in grid]
    positions = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        top, bottom = sorted((r1, r2))
        left, right = sorted((c1, c2))
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if r in (top, bottom) or c in (left, right):
                    out[r][c] = color
    return out
