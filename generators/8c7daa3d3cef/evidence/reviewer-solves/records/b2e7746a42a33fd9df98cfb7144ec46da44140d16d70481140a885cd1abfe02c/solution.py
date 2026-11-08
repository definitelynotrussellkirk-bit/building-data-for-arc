def solve(grid):
    """Fill the moat between an outer 4-frame and an inner 1-frame with 8."""
    out = [row[:] for row in grid]

    def bbox(color):
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if not cells:
            return None
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        return min(rows), max(rows), min(cols), max(cols)

    outer = bbox(4)
    inner = bbox(1)
    if outer is None or inner is None:
        return out

    outer_top, outer_bottom, outer_left, outer_right = outer
    inner_top, inner_bottom, inner_left, inner_right = inner

    for r in range(outer_top + 1, outer_bottom):
        for c in range(outer_left + 1, outer_right):
            inside_inner_box = (
                inner_top <= r <= inner_bottom
                and inner_left <= c <= inner_right
            )
            if out[r][c] == 0 and not inside_inner_box:
                out[r][c] = 8

    return out
