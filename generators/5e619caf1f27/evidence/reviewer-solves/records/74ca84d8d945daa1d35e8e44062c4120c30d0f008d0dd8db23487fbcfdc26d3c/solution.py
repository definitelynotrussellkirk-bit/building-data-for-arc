from collections import Counter


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), max(rows), min(cols), max(cols)


def solve(grid):
    """Add the next alternating rectangular frame around the nonzero object.

    The input contains an outer solid rectangular layer and an inner rectangle
    of a second color.  The common (modal) margin between the two rectangles is
    the layer thickness.  The next layer uses the inner color and is painted
    outside the current object's bounding box, clipped to the canvas.
    """
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]

    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return out
    top, bottom, left, right = _bbox(nonzero)

    colors = sorted({grid[r][c] for r, c in nonzero})
    if len(colors) < 2:
        return out

    # The inner color is the color whose bounding box is strictly contained in
    # the whole object's bounding box.  Prefer the most deeply inset candidate.
    candidates = []
    for color in colors:
        cells = [(r, c) for r, c in nonzero if grid[r][c] == color]
        ct, cb, cl, cr = _bbox(cells)
        margins = (ct - top, bottom - cb, cl - left, right - cr)
        if min(margins) > 0:
            candidates.append((sum(margins), -len(cells), color, (ct, cb, cl, cr), margins))

    if not candidates:
        return out
    _, _, inner_color, _, margins = max(candidates)

    counts = Counter(margins)
    # All authored examples have an unambiguous majority.  Median is a stable
    # fallback for a 2-2 tie while still representing the dominant scale.
    thickness = max(counts, key=lambda x: (counts[x], -abs(x - sorted(margins)[len(margins)//2])))
    if thickness <= 0:
        return out

    nt = max(0, top - thickness)
    nb = min(h - 1, bottom + thickness)
    nl = max(0, left - thickness)
    nr = min(w - 1, right + thickness)

    for r in range(nt, nb + 1):
        for c in range(nl, nr + 1):
            if top <= r <= bottom and left <= c <= right:
                continue
            out[r][c] = inner_color
    return out
