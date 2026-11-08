def solve(grid):
    """Crop the red frame and enlarge the enclosed colored motif to fill it."""
    frame_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if not frame_cells:
        return [row[:] for row in grid]

    top = min(r for r, _ in frame_cells)
    bottom = max(r for r, _ in frame_cells)
    left = min(c for _, c in frame_cells)
    right = max(c for _, c in frame_cells)

    height = bottom - top + 1
    width = right - left + 1
    out = [[0 for _ in range(width)] for _ in range(height)]

    for c in range(width):
        out[0][c] = 2
        out[-1][c] = 2
    for r in range(height):
        out[r][0] = 2
        out[r][-1] = 2

    motif_cells = [
        (r, c)
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] not in (0, 2)
    ]
    if not motif_cells:
        return out

    motif_top = min(r for r, _ in motif_cells)
    motif_bottom = max(r for r, _ in motif_cells)
    motif_left = min(c for _, c in motif_cells)
    motif_right = max(c for _, c in motif_cells)

    motif = [
        grid[r][motif_left : motif_right + 1]
        for r in range(motif_top, motif_bottom + 1)
    ]
    motif_h = len(motif)
    motif_w = len(motif[0])
    interior_h = height - 2
    interior_w = width - 2

    for r in range(interior_h):
        source_r = (r * motif_h) // interior_h
        for c in range(interior_w):
            source_c = (c * motif_w) // interior_w
            out[r + 1][c + 1] = motif[source_r][source_c]

    return out
