"""Visible-example-only solution for blind ARC episode ec9340d27f7e."""


def solve(grid):
    """Fill one-cell horizontal gaps whose neighbors share a nonzero color."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c in range(1, len(row) - 1):
            color = row[c - 1]
            if row[c] == 0 and color != 0 and row[c + 1] == color:
                out[r][c] = color
    return out
