"""Visible-only solution for blind task cf5ccd73cfe5."""
from collections import Counter


def _crop_points(grid, predicate):
    pts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if predicate(v)]
    if not pts:
        return []
    r0 = min(r for r, _ in pts)
    r1 = max(r for r, _ in pts)
    c0 = min(c for _, c in pts)
    c1 = max(c for _, c in pts)
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def solve(grid):
    """Scale the small motif to the interior of the large rectangular frame."""
    counts = Counter(v for row in grid for v in row if v != 0)
    if len(counts) < 2:
        return [list(row) for row in grid]

    frame_color = max(counts, key=lambda c: (counts[c], -c))
    frame_cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
                   if v == frame_color]
    r0 = min(r for r, _ in frame_cells)
    r1 = max(r for r, _ in frame_cells)
    c0 = min(c for _, c in frame_cells)
    c1 = max(c for _, c in frame_cells)

    motif = _crop_points(grid, lambda v: v not in (0, frame_color))
    mh = len(motif)
    mw = len(motif[0]) if motif else 0
    oh = r1 - r0 + 1
    ow = c1 - c0 + 1
    ih, iw = oh - 2, ow - 2
    if not motif or ih <= 0 or iw <= 0 or ih % mh or iw % mw:
        return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]

    sy, sx = ih // mh, iw // mw
    out = [[0] * ow for _ in range(oh)]
    for r in range(oh):
        out[r][0] = out[r][-1] = frame_color
    for c in range(ow):
        out[0][c] = out[-1][c] = frame_color
    for mr, row in enumerate(motif):
        for mc, value in enumerate(row):
            for dr in range(sy):
                for dc in range(sx):
                    out[1 + mr * sy + dr][1 + mc * sx + dc] = value
    return out
