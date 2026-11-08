from collections import Counter, defaultdict


def solve(grid):
    """Fill the axis-aligned rectangle spanned by every color occurring twice."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    cells = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                cells[color].append((r, c))

    out = [[0 for _ in range(w)] for _ in range(h)]
    for color, points in cells.items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r][c] = color
    return out
