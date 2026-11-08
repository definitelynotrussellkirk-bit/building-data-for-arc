from __future__ import annotations


def solve(grid):
    """Fill the comparison table encoded by the top and left 2x2 keys."""
    out = [list(row) for row in grid]
    if not out or not out[0]:
        return out

    height, width = len(out), len(out[0])

    # The first blank separator row/column bounds the 2x2 key area.
    separator_row = next(
        (r for r, row in enumerate(out) if all(value == 0 for value in row)),
        None,
    )
    separator_col = next(
        (c for c in range(width) if all(out[r][c] == 0 for r in range(height))),
        None,
    )
    if separator_row is None or separator_col is None:
        return out

    block_h, block_w = separator_row, separator_col
    if block_h <= 0 or block_w <= 0:
        return out

    row_starts = list(range(separator_row + 1, height, block_h + 1))
    col_starts = list(range(separator_col + 1, width, block_w + 1))

    column_counts = []
    for c0 in col_starts:
        count = sum(
            out[r][c] != 0
            for r in range(block_h)
            for c in range(c0, min(c0 + block_w, width))
        )
        column_counts.append(count)

    for r0 in row_starts:
        row_count = sum(
            out[r][c] != 0
            for r in range(r0, min(r0 + block_h, height))
            for c in range(block_w)
        )
        for c0, column_count in zip(col_starts, column_counts):
            fill = 3 if row_count > column_count else 4 if row_count < column_count else 8
            for r in range(r0, min(r0 + block_h, height)):
                for c in range(c0, min(c0 + block_w, width)):
                    out[r][c] = fill
    return out
