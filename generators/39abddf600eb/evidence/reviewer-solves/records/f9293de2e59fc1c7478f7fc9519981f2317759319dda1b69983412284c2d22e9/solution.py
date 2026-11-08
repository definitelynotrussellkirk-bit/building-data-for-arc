"""Visible-example solution for reviewer episode 39abddf600eb."""
from collections import Counter


def solve(grid):
    out = [row[:] for row in grid]
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return out

    # The frame is the repeated nonzero color; the two seeds are the remaining
    # nonzero cells strictly inside its rectangular border.
    frame_color = max(counts, key=counts.get)
    frame_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == frame_color
    ]
    r1 = min(r for r, _ in frame_cells)
    r2 = max(r for r, _ in frame_cells)
    c1 = min(c for _, c in frame_cells)
    c2 = max(c for _, c in frame_cells)

    seeds = [
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if grid[r][c] not in (0, frame_color)
    ]
    if len(seeds) != 2:
        return out
    (ar, ac), (br, bc) = seeds

    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            da = abs(r - ar) + abs(c - ac)
            db = abs(r - br) + abs(c - bc)
            if da == db:
                out[r][c] = 9
    return out
