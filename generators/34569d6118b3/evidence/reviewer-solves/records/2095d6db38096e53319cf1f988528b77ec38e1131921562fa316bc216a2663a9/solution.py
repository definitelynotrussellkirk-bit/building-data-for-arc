"""Visible-example solution for the blind ARC task.

The input contains three colour keys at upper left, three binary glyphs drawn
in colour 5 at upper right, and a lower rectangular colour matrix.  Replace
each matrix entry by the glyph associated with that colour, painting the glyph
with the matrix colour and leaving the rest background 0.
"""


def _runs(values):
    """Return inclusive-exclusive runs of truthy entries."""
    out = []
    start = None
    for i, value in enumerate(values + [False]):
        if value and start is None:
            start = i
        elif not value and start is not None:
            out.append((start, i))
            start = None
    return out


def solve(grid):
    if not grid or not grid[0]:
        return []

    h, w = len(grid), len(grid[0])
    template_colour = 5

    # The glyph bank is the only region drawn in colour 5.  Its occupied
    # columns form one run per glyph; the fully painted top edge guarantees
    # that a glyph's slot is not split by an internally blank column.
    five_rows = [r for r in range(h) if any(grid[r][c] == template_colour for c in range(w))]
    if not five_rows:
        raise ValueError("no colour-5 glyph bank found")
    glyph_h = max(five_rows) + 1
    occupied_cols = [any(grid[r][c] == template_colour for r in range(glyph_h)) for c in range(w)]
    glyph_runs = _runs(occupied_cols)
    if not glyph_runs:
        raise ValueError("no glyph slots found")

    glyphs = [
        [[grid[r][c] == template_colour for c in range(c0, c1)] for r in range(glyph_h)]
        for c0, c1 in glyph_runs
    ]

    # Read the colour legend from the first row before the glyph bank,
    # collapsing the repeated cells used to draw each swatch.
    legend_end = glyph_runs[0][0]
    keys = []
    previous = None
    for colour in grid[0][:legend_end]:
        if colour in (0, template_colour):
            previous = None
            continue
        if colour != previous:
            keys.append(colour)
        previous = colour

    if len(keys) != len(glyphs):
        raise ValueError(f"legend/glyph mismatch: {len(keys)} keys, {len(glyphs)} glyphs")
    if len(set(keys)) != len(keys):
        raise ValueError("legend colours must be distinct")
    glyph_for = dict(zip(keys, glyphs))

    # Everything coloured below the glyph bank belongs to the dense matrix.
    lower = [(r, c) for r in range(glyph_h, h) for c in range(w) if grid[r][c] != 0]
    if not lower:
        raise ValueError("no lower colour matrix found")
    r0 = min(r for r, _ in lower)
    r1 = max(r for r, _ in lower) + 1
    c0 = min(c for _, c in lower)
    c1 = max(c for _, c in lower) + 1
    matrix = [row[c0:c1] for row in grid[r0:r1]]

    if any(colour not in glyph_for for row in matrix for colour in row):
        raise ValueError("matrix contains background or an unkeyed colour")

    glyph_w = len(glyphs[0][0])
    if any(len(glyph) != glyph_h or any(len(row) != glyph_w for row in glyph) for glyph in glyphs):
        raise ValueError("glyph slots do not share one shape")

    out = [[0] * (len(matrix[0]) * glyph_w) for _ in range(len(matrix) * glyph_h)]
    for mr, row in enumerate(matrix):
        for mc, colour in enumerate(row):
            glyph = glyph_for[colour]
            for gr in range(glyph_h):
                for gc in range(glyph_w):
                    if glyph[gr][gc]:
                        out[mr * glyph_h + gr][mc * glyph_w + gc] = colour
    return out
