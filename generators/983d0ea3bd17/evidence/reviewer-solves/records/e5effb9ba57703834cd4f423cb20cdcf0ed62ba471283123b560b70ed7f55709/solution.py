"""Visible-only solution for blind task 983d0ea3bd17."""


def solve(grid):
    """Extend orange rays from every red cell until an opaque non-red cell."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    original = [row[:] for row in grid]
    out = [row[:] for row in grid]

    sources = [
        (r, c)
        for r in range(height)
        for c in range(width)
        if original[r][c] == 2
    ]
    for r, c in sources:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            while 0 <= rr < height and 0 <= cc < width:
                value = original[rr][cc]
                if value not in (0, 2):
                    break
                if value == 0:
                    out[rr][cc] = 7
                rr += dr
                cc += dc
    return out
