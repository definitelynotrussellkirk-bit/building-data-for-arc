def solve(grid):
    """Fill row/column intersections indicated by the visible marker scheme."""
    out = [row[:] for row in grid]
    if not out:
        return out

    marked_columns = [c for c, value in enumerate(out[0]) if value == 2]
    marked_rows = [r for r, row in enumerate(out) if 1 in row]

    for r in marked_rows:
        for c in marked_columns:
            if out[r][c] == 0:
                out[r][c] = 3
    return out
