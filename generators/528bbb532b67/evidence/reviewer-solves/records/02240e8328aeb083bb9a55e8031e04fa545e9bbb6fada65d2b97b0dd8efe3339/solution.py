def solve(grid):
    """Mirror every colored motif cell across the vertical axis of the 8-frame."""
    out = [row[:] for row in grid]
    frame_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if not frame_cells:
        return out

    left = min(c for _, c in frame_cells)
    right = max(c for _, c in frame_cells)

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 8) and left < c < right:
                mirror_c = left + right - c
                if 0 <= mirror_c < len(row):
                    out[r][mirror_c] = value
    return out
