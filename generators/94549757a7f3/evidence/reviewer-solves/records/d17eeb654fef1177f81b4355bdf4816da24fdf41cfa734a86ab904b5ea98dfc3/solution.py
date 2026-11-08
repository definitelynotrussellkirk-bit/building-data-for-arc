"""Extend each horizontal green run by a single red cell, when space is empty."""
def solve(grid):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] != 3:
                c += 1
                continue
            start = c
            while c < len(row) and row[c] == 3:
                c += 1
            if c - start >= 2 and c < len(row) and row[c] == 0:
                out[r][c] = 2
    return out
