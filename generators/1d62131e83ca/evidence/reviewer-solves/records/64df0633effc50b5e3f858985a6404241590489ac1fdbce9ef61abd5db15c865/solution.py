def solve(grid):
    """Extend color 1 northwest and color 2 southeast to the border."""
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    ones = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    twos = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]

    if ones:
        r = min(r for r, _ in ones) - 1
        c = min(c for _, c in ones) - 1
        while r >= 0 and c >= 0:
            out[r][c] = 1
            r -= 1
            c -= 1

    if twos:
        r = max(r for r, _ in twos) + 1
        c = max(c for _, c in twos) + 1
        while r < height and c < width:
            out[r][c] = 2
            r += 1
            c += 1

    return out
