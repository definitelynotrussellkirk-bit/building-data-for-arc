from collections import defaultdict


def solve(grid):
    """Draw each same-colour pair's axis-aligned bounding-box perimeter."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            # The visible task uses exactly two markers per colour.  Preserve
            # unsupported colours rather than inventing extra geometry.
            continue
        (r1, c1), (r2, c2) = cells
        top, bottom = sorted((r1, r2))
        left, right = sorted((c1, c2))
        for c in range(left, right + 1):
            out[top][c] = color
            out[bottom][c] = color
        for r in range(top, bottom + 1):
            out[r][left] = color
            out[r][right] = color
    return out
