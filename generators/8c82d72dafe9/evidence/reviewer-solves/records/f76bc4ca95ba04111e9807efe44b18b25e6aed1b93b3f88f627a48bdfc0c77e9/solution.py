from __future__ import annotations


def solve(grid):
    """Expand diagonal equal-color marker pairs into rectangle borders."""
    if not isinstance(grid, list) or not grid:
        return grid
    out = [list(row) for row in grid]
    positions = {}
    # Python dictionaries retain first-insertion order, matching the visible
    # examples' row-major first-occurrence precedence at border intersections.
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r_a, c_a), (r_b, c_b) = cells
        if r_a == r_b or c_a == c_b:
            # The two 5s in train 2 and two 3s in train 1 are collinear and
            # remain unchanged, so a genuine rectangle needs both dimensions.
            continue
        r0, r1 = sorted((r_a, r_b))
        c0, c1 = sorted((c_a, c_b))
        for c in range(c0, c1 + 1):
            out[r0][c] = color
            out[r1][c] = color
        for r in range(r0, r1 + 1):
            out[r][c0] = color
            out[r][c1] = color
    return out
