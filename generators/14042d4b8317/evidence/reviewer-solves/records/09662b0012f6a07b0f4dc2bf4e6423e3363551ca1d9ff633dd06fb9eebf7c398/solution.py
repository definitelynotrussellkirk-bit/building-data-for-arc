from collections import defaultdict


def solve(grid):
    """Complete each same-colour three-corner axis-aligned rectangle."""
    out = [row[:] for row in grid]
    cells_by_colour = defaultdict(list)

    for r, row in enumerate(grid):
        for c, colour in enumerate(row):
            if colour != 0:
                cells_by_colour[colour].append((r, c))

    for colour, cells in cells_by_colour.items():
        rows = {r for r, _ in cells}
        cols = {c for _, c in cells}
        if len(cells) == 3 and len(rows) == 2 and len(cols) == 2:
            occupied = set(cells)
            missing = [(r, c) for r in rows for c in cols if (r, c) not in occupied]
            if len(missing) == 1:
                r, c = missing[0]
                out[r][c] = colour

    return out
