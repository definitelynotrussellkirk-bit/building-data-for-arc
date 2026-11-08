from collections import defaultdict


def solve(grid):
    """Connect repeated same-color cells across each row.

    For every nonzero color appearing at least twice in a row, fill background
    cells between its leftmost and rightmost occurrences with that color.
    Existing nonzero cells are preserved.
    """
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        positions = defaultdict(list)
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append(c)
        for color, cols in positions.items():
            if len(cols) < 2:
                continue
            for c in range(cols[0], cols[-1] + 1):
                if out[r][c] == 0:
                    out[r][c] = color
    return out
