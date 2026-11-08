def solve(grid):
    """Rotate the color-3 glyph clockwise into the frame's upper-left corner."""
    out = [row[:] for row in grid]

    marker_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    frame_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 3)
    ]
    if not marker_cells or not frame_cells:
        return out

    # Remove the source glyph.
    for r, c in marker_cells:
        out[r][c] = 0

    marker_top = min(r for r, _ in marker_cells)
    marker_bottom = max(r for r, _ in marker_cells)
    marker_left = min(c for _, c in marker_cells)
    marker_right = max(c for _, c in marker_cells)
    marker_height = marker_bottom - marker_top + 1
    marker_width = marker_right - marker_left + 1

    glyph = [[False] * marker_width for _ in range(marker_height)]
    for r, c in marker_cells:
        glyph[r - marker_top][c - marker_left] = True

    # Clockwise rotation: HxW -> WxH.
    rotated = [
        [glyph[marker_height - 1 - r][c] for r in range(marker_height)]
        for c in range(marker_width)
    ]

    frame_top = min(r for r, _ in frame_cells)
    frame_left = min(c for _, c in frame_cells)
    anchor_row = frame_top + 1
    anchor_col = frame_left + 1

    for dr, row in enumerate(rotated):
        for dc, filled in enumerate(row):
            if filled:
                out[anchor_row + dr][anchor_col + dc] = 3
    return out
