from collections import Counter


def _rotate_cw(mask):
    """Rotate a rectangular list-of-lists 90 degrees clockwise."""
    return [list(row) for row in zip(*mask[::-1])]


def solve(grid):
    """Stamp the colored template at orientation markers 2, 3, 4 and 5.

    Marker 2 uses the template as-is, 3/4/5 rotate it clockwise by
    90/180/270 degrees.  Each marker is the top-left of the rotated
    bounding box; cells outside the canvas are clipped.
    """
    h, w = len(grid), len(grid[0])
    counts = Counter(v for row in grid for v in row if v)

    # The template is the only non-background color occupying multiple cells.
    template_color = max(counts, key=lambda color: counts[color])
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == template_color
    ]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    mask = [
        [grid[r][c] == template_color for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]

    rotations = {2: mask}
    for marker in (3, 4, 5):
        rotations[marker] = _rotate_cw(rotations[marker - 1])

    out = [[0] * w for _ in range(h)]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            oriented = rotations.get(value)
            if oriented is None or value == template_color:
                continue
            for dr, oriented_row in enumerate(oriented):
                rr = r + dr
                if rr >= h:
                    break
                for dc, filled in enumerate(oriented_row):
                    cc = c + dc
                    if cc >= w:
                        break
                    if filled:
                        out[rr][cc] = template_color
    return out
