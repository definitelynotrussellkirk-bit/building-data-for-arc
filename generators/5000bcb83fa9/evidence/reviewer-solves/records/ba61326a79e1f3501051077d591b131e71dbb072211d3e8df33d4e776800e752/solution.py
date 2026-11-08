"""Visible-example solution for task 5000bcb83fa9."""


def solve(grid):
    """Collapse each maximal nonzero horizontal run to its middle cell."""
    output = [[0 for _ in row] for row in grid]
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            start = c
            color = row[c]
            while c < len(row) and row[c] == color:
                c += 1
            length = c - start
            output[r][start + length // 2] = color
    return output
