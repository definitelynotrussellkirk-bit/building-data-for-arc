"""Visible-example-only solution for blind task 0b8ba9bb3c63."""


def solve(grid):
    """Extend the color-8 rectangle's rows/columns as color-4 rays.

    Background (0) and red cells (2) are transparent/repaintable.  A cell of
    any other color blocks that individual ray, and the blocker is preserved.
    """
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    eight_cells = [
        (r, c)
        for r, row in enumerate(out)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not eight_cells:
        return out

    top = min(r for r, _ in eight_cells)
    bottom = max(r for r, _ in eight_cells)
    left = min(c for _, c in eight_cells)
    right = max(c for _, c in eight_cells)

    def paint_ray(r, c, dr, dc):
        while 0 <= r < height and 0 <= c < width:
            value = out[r][c]
            if value in (0, 2):
                out[r][c] = 4
            else:
                break
            r += dr
            c += dc

    for r in range(top, bottom + 1):
        paint_ray(r, left - 1, 0, -1)
        paint_ray(r, right + 1, 0, 1)

    for c in range(left, right + 1):
        paint_ray(top - 1, c, -1, 0)
        paint_ray(bottom + 1, c, 1, 0)

    return out
