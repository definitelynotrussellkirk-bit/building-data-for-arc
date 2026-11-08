"""Visible-example-only solution for the blind ARC episode."""


def solve(grid):
    """Move the 3x3 panel containing color 4 to the panel indexed by the 4.

    The input is a 3x3 array of panels separated by solid divider rows and
    columns.  All ordinary panel cells are erased.  The complete panel that
    contains the unique color-4 marker is copied to destination panel
    ``(marker_local_row, marker_local_col)``.
    """
    height = len(grid)
    width = len(grid[0])

    divider_rows = [
        r for r, row in enumerate(grid)
        if row and row[0] != 0 and all(value == row[0] for value in row)
    ]
    divider_cols = [
        c for c in range(width)
        if grid[0][c] != 0 and all(grid[r][c] == grid[0][c] for r in range(height))
    ]

    row_starts = [0] + [r + 1 for r in divider_rows]
    row_ends = divider_rows + [height]
    col_starts = [0] + [c + 1 for c in divider_cols]
    col_ends = divider_cols + [width]

    marker = None
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 4:
                marker = (r, c)
                break
        if marker is not None:
            break
    if marker is None:
        raise ValueError("expected one color-4 marker")

    marker_r, marker_c = marker
    source_panel_r = next(i for i, (a, b) in enumerate(zip(row_starts, row_ends)) if a <= marker_r < b)
    source_panel_c = next(i for i, (a, b) in enumerate(zip(col_starts, col_ends)) if a <= marker_c < b)
    local_r = marker_r - row_starts[source_panel_r]
    local_c = marker_c - col_starts[source_panel_c]

    if local_r >= len(row_starts) or local_c >= len(col_starts):
        raise ValueError("marker position does not identify a destination panel")

    result = [[0 for _ in range(width)] for _ in range(height)]
    for r in divider_rows:
        result[r] = list(grid[r])
    for c in divider_cols:
        for r in range(height):
            result[r][c] = grid[r][c]

    src_r0, src_r1 = row_starts[source_panel_r], row_ends[source_panel_r]
    src_c0, src_c1 = col_starts[source_panel_c], col_ends[source_panel_c]
    dst_r0, dst_r1 = row_starts[local_r], row_ends[local_r]
    dst_c0, dst_c1 = col_starts[local_c], col_ends[local_c]

    source = [row[src_c0:src_c1] for row in grid[src_r0:src_r1]]
    if (src_r1 - src_r0, src_c1 - src_c0) != (dst_r1 - dst_r0, dst_c1 - dst_c0):
        raise ValueError("source and destination panels have different shapes")

    for dr, row in enumerate(source):
        result[dst_r0 + dr][dst_c0:dst_c1] = row

    return result
