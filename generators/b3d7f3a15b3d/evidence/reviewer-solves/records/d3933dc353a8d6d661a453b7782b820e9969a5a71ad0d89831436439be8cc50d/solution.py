"""Visible-example solution for the framed-cell propagation puzzle."""
from collections import Counter


def solve(grid):
    h, w = len(grid), len(grid[0])

    def zero_row(r):
        return all(grid[r][c] == 0 for c in range(w))

    def zero_col(c):
        return all(grid[r][c] == 0 for r in range(h))

    row_starts = [
        r for r in range(h)
        if not zero_row(r) and (r == 0 or zero_row(r - 1))
    ]
    col_starts = [
        c for c in range(w)
        if not zero_col(c) and (c == 0 or zero_col(c - 1))
    ]
    if not row_starts or not col_starts:
        return [row[:] for row in grid]

    def block_end(start, limit, is_separator):
        for x in range(start, limit):
            if is_separator(x):
                return x - 1
        return limit - 1

    block_h = block_end(row_starts[0], h, zero_row) - row_starts[0] + 1
    block_w = block_end(col_starts[0], w, zero_col) - col_starts[0] + 1

    interior = [
        grid[rs + dr][cs + dc]
        for rs in row_starts
        for cs in col_starts
        for dr in range(1, block_h - 1)
        for dc in range(1, block_w - 1)
    ]
    common = Counter(interior).most_common(1)[0][0]
    colors = sorted({value for row in grid for value in row} - {0, common})

    out = [row[:] for row in grid]
    for color in colors:
        for dr in range(1, block_h - 1):
            for dc in range(1, block_w - 1):
                for i, rs in enumerate(row_starts):
                    columns = [
                        j for j, cs in enumerate(col_starts)
                        if grid[rs + dr][cs + dc] == color
                    ]
                    if len(columns) >= 2:
                        for j in range(min(columns), max(columns) + 1):
                            out[rs + dr][col_starts[j] + dc] = color

                for j, cs in enumerate(col_starts):
                    rows = [
                        i for i, rs in enumerate(row_starts)
                        if grid[rs + dr][cs + dc] == color
                    ]
                    if len(rows) >= 2:
                        for i in range(min(rows), max(rows) + 1):
                            out[row_starts[i] + dr][cs + dc] = color
    return out
