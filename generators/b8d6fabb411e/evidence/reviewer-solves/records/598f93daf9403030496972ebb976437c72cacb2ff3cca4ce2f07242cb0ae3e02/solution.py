"""Visible-example solution for blind task b8d6fabb411e."""


def solve(grid):
    """Connect every orthogonally aligned colored marker to the green block.

    The green (3) cells form one solid rectangle.  Any other non-background
    cell whose row intersects that rectangle, or whose column intersects it,
    paints the zero-valued gap between itself and the rectangle with its own
    color.  Unaligned markers are unchanged.
    """
    out = [row[:] for row in grid]

    green = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    if not green:
        return out

    top = min(r for r, _ in green)
    bottom = max(r for r, _ in green)
    left = min(c for _, c in green)
    right = max(c for _, c in green)

    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 3)
    ]

    for r, c, color in markers:
        if top <= r <= bottom:
            if c < left:
                for cc in range(c + 1, left):
                    if out[r][cc] == 0:
                        out[r][cc] = color
            elif c > right:
                for cc in range(right + 1, c):
                    if out[r][cc] == 0:
                        out[r][cc] = color

        if left <= c <= right:
            if r < top:
                for rr in range(r + 1, top):
                    if out[rr][c] == 0:
                        out[rr][c] = color
            elif r > bottom:
                for rr in range(bottom + 1, r):
                    if out[rr][c] == 0:
                        out[rr][c] = color

    return out
