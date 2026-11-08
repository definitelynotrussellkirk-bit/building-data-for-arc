"""Visible-example solution for task c24bb478ceb4."""


def solve(grid):
    out = [row[:] for row in grid]
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color.setdefault(value, []).append((r, c))

    for color, cells in by_color.items():
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if len(cells) != 3 or len(rows) != 2 or len(cols) != 2:
            continue
        present = set(cells)
        for r in rows:
            for c in cols:
                if (r, c) not in present:
                    out[r][c] = color
    return out
