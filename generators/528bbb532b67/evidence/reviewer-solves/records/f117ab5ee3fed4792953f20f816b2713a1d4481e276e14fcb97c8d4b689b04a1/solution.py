def solve(grid):
    """Mirror the left half of the pattern inside the color-8 frame."""
    out = [row[:] for row in grid]
    frame_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not frame_cells:
        return out

    top = min(r for r, _ in frame_cells)
    bottom = max(r for r, _ in frame_cells)
    left = min(c for _, c in frame_cells)
    right = max(c for _, c in frame_cells)

    # The examples place the source motif in the left half of the framed
    # interior. Reflect every source cell, including background cells, across
    # the frame's vertical axis. This works for both even and odd interiors.
    for r in range(top + 1, bottom):
        for c in range(left + 1, (left + right) // 2 + 1):
            out[r][left + right - c] = grid[r][c]
    return out
