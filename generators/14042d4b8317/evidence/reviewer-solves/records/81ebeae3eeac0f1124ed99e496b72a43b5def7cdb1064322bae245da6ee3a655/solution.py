"""Blind solution for task 14042d4b8317.

For each non-background colour, the three marked cells are three corners of an
axis-aligned rectangle.  Complete the missing fourth corner with that colour.
"""


def solve(grid):
    out = [row[:] for row in grid]
    colours = sorted({value for row in grid for value in row if value != 0})

    for colour in colours:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == colour
        ]
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})

        if len(cells) == 3 and len(rows) == 2 and len(cols) == 2:
            occupied = set(cells)
            missing = [
                (r, c)
                for r in rows
                for c in cols
                if (r, c) not in occupied
            ]
            if len(missing) == 1:
                r, c = missing[0]
                out[r][c] = colour

    return out
