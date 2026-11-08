from collections import defaultdict


def solve(grid):
    """Connect same-colour markers that share a row or column."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                positions[color].append((r, c))

    for color, cells in positions.items():
        # Every collinear pair contributes its inclusive horizontal/vertical span.
        # This also handles a colour with an extra unpaired marker.
        for i, (r1, c1) in enumerate(cells):
            for r2, c2 in cells[i + 1 :]:
                if r1 == r2:
                    lo, hi = sorted((c1, c2))
                    for c in range(lo, hi + 1):
                        out[r1][c] = color
                elif c1 == c2:
                    lo, hi = sorted((r1, r2))
                    for r in range(lo, hi + 1):
                        out[r][c1] = color
    return out
