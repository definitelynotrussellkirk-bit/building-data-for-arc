"""Visible-example solution for the post-repair episode."""


def solve(grid):
    """Flood each colored seed through its 4-connected zero region.

    Color 5 is a wall.  Every other nonzero color is a seed.  Seedless zero
    components stay zero.  Seeds are processed in row-major order so the
    implementation remains defined even if a future visible instance contains
    more than one seed in the same region.
    """
    out = [list(row) for row in grid]
    height = len(out)
    width = len(out[0])
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    for sr, sc, color in seeds:
        out[sr][sc] = 0
        stack = [(sr, sc)]
        while stack:
            r, c = stack.pop()
            if not (0 <= r < height and 0 <= c < width):
                continue
            if out[r][c] != 0:
                continue
            out[r][c] = color
            stack.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
    return out
