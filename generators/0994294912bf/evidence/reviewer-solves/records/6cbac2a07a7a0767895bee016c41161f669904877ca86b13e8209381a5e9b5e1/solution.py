"""Visible-example-only solution for blind task 0994294912bf."""


def solve(grid):
    """Copy the lower-left object's 4-neighbour boundary to the lower-right panel."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    sep_rows = [r for r, row in enumerate(grid) if row and all(v == 9 for v in row)]
    sep_cols = [
        c
        for c in range(width)
        if all(len(row) > c and row[c] == 9 for row in grid)
    ]
    if not sep_rows or not sep_cols:
        return out

    sep_r = sep_rows[0]
    sep_c = sep_cols[0]
    src_h = height - sep_r - 1
    src_w = sep_c
    dst_h = src_h
    dst_w = width - sep_c - 1

    occupied = {
        (r, c)
        for r in range(src_h)
        for c in range(src_w)
        if grid[sep_r + 1 + r][c] not in (0, 9)
    }
    if not occupied:
        return out

    first_r, first_c = min(occupied)
    paint = grid[sep_r + 1 + first_r][first_c]

    for r, c in occupied:
        is_boundary = any(
            (r + dr, c + dc) not in occupied
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        if is_boundary and r < dst_h and c < dst_w:
            out[sep_r + 1 + r][sep_c + 1 + c] = paint

    return out
