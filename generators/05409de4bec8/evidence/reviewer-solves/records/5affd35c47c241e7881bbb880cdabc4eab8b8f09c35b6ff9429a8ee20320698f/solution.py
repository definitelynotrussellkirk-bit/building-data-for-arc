"""Visible-example solution for review task 05409de4bec8."""
from __future__ import annotations

from collections import Counter


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    counts = Counter(value for row in grid for value in row if value != 0)

    candidates = []
    for color, count in counts.items():
        if count != 4:
            continue
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if len(rows) <= 3 and len(cols) <= 3:
            pair_rows = [r for r in rows if sum(rr == r for rr, _ in cells) == 2]
            pair_cols = [c for c in cols if sum(cc == c for _, cc in cells) == 2]
            # Prefer the four-cell signal with the strongest repeated-axis structure.
            candidates.append((len(pair_rows) + len(pair_cols), color, cells, rows, cols,
                               pair_rows, pair_cols))

    if not candidates:
        raise ValueError("no four-cell signal color found")
    _, color, cells, rows, cols, pair_rows, pair_cols = max(candidates)

    out = [[0] * width for _ in range(height)]
    is_rectangle = (
        len(rows) == 2
        and len(cols) == 2
        and set(cells) == {(r, c) for r in rows for c in cols}
    )

    if is_rectangle:
        row_span = rows[-1] - rows[0]
        col_span = cols[-1] - cols[0]
        # Extend the two sides parallel to the rectangle's longer separation.
        if row_span > col_span:
            draw_rows, draw_cols = [], cols
        else:
            draw_rows, draw_cols = rows, []
    else:
        draw_rows, draw_cols = pair_rows, pair_cols

    for r in range(height):
        for c in range(width):
            if r in draw_rows or c in draw_cols:
                out[r][c] = color
    return out
