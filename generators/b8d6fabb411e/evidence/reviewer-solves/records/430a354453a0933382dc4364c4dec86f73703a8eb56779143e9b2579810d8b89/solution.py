"""Visible-example solution for the reviewer-authored b8d6fabb411e episode."""


def solve(grid):
    """Connect aligned colored markers to the nearest edge of the solid 3-square."""
    out = [row[:] for row in grid]
    threes = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    if not threes:
        return out

    top = min(r for r, _ in threes)
    bottom = max(r for r, _ in threes)
    left = min(c for _, c in threes)
    right = max(c for _, c in threes)

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 3):
                continue

            if top <= r <= bottom:
                if c < left:
                    for cc in range(c + 1, left):
                        out[r][cc] = value
                elif c > right:
                    for cc in range(right + 1, c):
                        out[r][cc] = value
            elif left <= c <= right:
                if r < top:
                    for rr in range(r + 1, top):
                        out[rr][c] = value
                elif r > bottom:
                    for rr in range(bottom + 1, r):
                        out[rr][c] = value

    return out
