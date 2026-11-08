"""Visible-example solution for blind task 6098a755202d."""


def solve(grid):
    """Color the interior of the gray frame by Manhattan-nearest marker.

    Gray (5) forms a rectangular frame.  Every other nonzero color inside the
    frame is a marker.  An interior background cell receives a color exactly
    when all nearest markers (Manhattan distance) have that same color; ties
    between different colors remain background.
    """
    out = [row[:] for row in grid]
    gray = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    if not gray:
        return out

    top = min(r for r, _ in gray)
    bottom = max(r for r, _ in gray)
    left = min(c for _, c in gray)
    right = max(c for _, c in gray)

    markers = [
        (r, c, grid[r][c])
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] not in (0, 5)
    ]
    if not markers:
        return out

    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            if grid[r][c] != 0:
                continue
            distances = [(abs(r - mr) + abs(c - mc), color) for mr, mc, color in markers]
            nearest_distance = min(distance for distance, _ in distances)
            nearest_colors = {
                color for distance, color in distances if distance == nearest_distance
            }
            if len(nearest_colors) == 1:
                out[r][c] = nearest_colors.pop()
    return out
