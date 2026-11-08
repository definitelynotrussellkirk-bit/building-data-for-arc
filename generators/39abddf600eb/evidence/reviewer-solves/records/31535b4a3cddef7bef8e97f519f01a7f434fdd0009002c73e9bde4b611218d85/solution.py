from collections import Counter


def solve(grid):
    """Paint the Manhattan-distance bisector of the two interior markers."""
    out = [row[:] for row in grid]
    counts = Counter(value for row in grid for value in row if value != 0)
    if len(counts) < 3:
        return out

    # The rectangular frame is the repeated non-background color.  The other
    # two non-background colors are the singleton sites whose L1 bisector is
    # drawn in color 9.
    frame_color = max(counts, key=counts.get)
    frame_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == frame_color
    ]
    if not frame_cells:
        return out

    top = min(r for r, _ in frame_cells)
    bottom = max(r for r, _ in frame_cells)
    left = min(c for _, c in frame_cells)
    right = max(c for _, c in frame_cells)

    markers = [
        (r, c)
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] not in (0, frame_color, 9)
    ]
    if len(markers) != 2:
        return out

    (r1, c1), (r2, c2) = markers
    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if grid[r][c] != 0:
                continue
            d1 = abs(r - r1) + abs(c - c1)
            d2 = abs(r - r2) + abs(c - c2)
            if d1 == d2:
                out[r][c] = 9
    return out
