from collections import defaultdict


def solve(grid):
    """Replace every colored object by the corners of its bounding box."""
    positions = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    out = [[0 for _ in row] for row in grid]
    for color, cells in positions.items():
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        for r, c in {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}:
            out[r][c] = color
    return out
