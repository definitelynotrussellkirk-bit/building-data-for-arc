"""Visible-example-only solution for the blind ARC puzzle."""


def _crop_nonzero(grid):
    rows = [r for r, row in enumerate(grid) if any(v != 0 for v in row)]
    cols = [c for c in range(len(grid[0])) if any(grid[r][c] != 0 for r in range(len(grid)))]
    if not rows or not cols:
        return [[0]]
    r0, r1 = rows[0], rows[-1]
    c0, c1 = cols[0], cols[-1]
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def solve(grid):
    """Expand the cropped motif fractally.

    Each non-background cell of the motif becomes one exact copy of the whole
    motif; each background cell becomes an equally sized zero block.  Keeping
    the copied motif's colors (rather than recoloring it by the outer cell)
    is the direct multicolor extension of all visible examples.
    """
    motif = _crop_nonzero(grid)
    h, w = len(motif), len(motif[0])
    out = [[0 for _ in range(w * w)] for _ in range(h * h)]
    for outer_r in range(h):
        for outer_c in range(w):
            if motif[outer_r][outer_c] == 0:
                continue
            for inner_r in range(h):
                for inner_c in range(w):
                    out[outer_r * h + inner_r][outer_c * w + inner_c] = motif[inner_r][inner_c]
    return out
