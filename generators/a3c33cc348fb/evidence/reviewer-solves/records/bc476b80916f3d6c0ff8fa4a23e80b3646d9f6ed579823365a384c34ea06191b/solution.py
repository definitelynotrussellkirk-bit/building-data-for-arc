from collections import Counter


def solve(grid):
    """Extend the two-color framed rectangle until its outer edge reaches marker 8."""
    h, w = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    marker_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if len(marker_cells) != 1:
        # Visible examples use a unique 8. Keep a conservative fallback for
        # malformed/unexpected inputs instead of producing a partial drawing.
        return [row[:] for row in grid]
    mr, mc = marker_cells[0]

    object_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background and (r, c) != (mr, mc)
    ]
    if not object_cells:
        return [row[:] for row in grid]

    r0 = min(r for r, _ in object_cells)
    r1 = max(r for r, _ in object_cells)
    c0 = min(c for _, c in object_cells)
    c1 = max(c for _, c in object_cells)

    # The original object is a filled rectangle with a one-cell frame.
    border = grid[r0][c0]
    interior_values = [
        grid[r][c]
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] != border
    ]
    interior = interior_values[0] if interior_values else border

    # The marker lies beyond exactly one side; that side becomes the new edge.
    if mr < r0:
        r0 = mr
    elif mr > r1:
        r1 = mr
    elif mc < c0:
        c0 = mc
    elif mc > c1:
        c1 = mc
    else:
        return [row[:] for row in grid]

    out = [[background for _ in range(w)] for _ in range(h)]
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r in (r0, r1) or c in (c0, c1):
                out[r][c] = border
            else:
                out[r][c] = interior
    return out
