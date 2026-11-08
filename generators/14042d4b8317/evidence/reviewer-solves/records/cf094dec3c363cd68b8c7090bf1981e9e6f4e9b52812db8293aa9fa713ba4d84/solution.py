from collections import defaultdict


def solve(grid):
    """Complete each color's axis-aligned rectangle from its three corners."""
    out = [row[:] for row in grid]
    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color[value].append((r, c))

    for color, cells in by_color.items():
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        # The visible examples use three corners of a 2x2 Cartesian product.
        if len(cells) == 3 and len(rows) == 2 and len(cols) == 2:
            occupied = set(cells)
            missing = {(r, c) for r in rows for c in cols} - occupied
            if len(missing) == 1:
                r, c = missing.pop()
                if out[r][c] == 0:
                    out[r][c] = color
    return out
