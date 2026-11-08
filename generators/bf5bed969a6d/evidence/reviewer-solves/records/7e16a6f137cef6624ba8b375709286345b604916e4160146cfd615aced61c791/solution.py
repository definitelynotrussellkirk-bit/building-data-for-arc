def solve(grid):
    """Stamp the red (2) motif, recolored, into every hollow frame."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    marker = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if not marker:
        return out

    marker_top = min(r for r, _ in marker)
    marker_left = min(c for _, c in marker)
    motif = [(r - marker_top, c - marker_left) for r, c in marker]
    motif_height = max(r for r, _ in motif) + 1
    motif_width = max(c for _, c in motif) + 1

    # The marker is a template, not part of the result.
    for r, c in marker:
        out[r][c] = 0

    frame_colors = sorted(
        {
            value
            for row in grid
            for value in row
            if value not in (0, 2)
        }
    )

    for color in frame_colors:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if not cells:
            continue

        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)

        inner_top, inner_bottom = top + 1, bottom - 1
        inner_left, inner_right = left + 1, right - 1
        inner_height = inner_bottom - inner_top + 1
        inner_width = inner_right - inner_left + 1
        if inner_height < motif_height or inner_width < motif_width:
            continue

        stamp_top = inner_top + (inner_height - motif_height) // 2
        stamp_left = inner_left + (inner_width - motif_width) // 2
        for dr, dc in motif:
            r = stamp_top + dr
            c = stamp_left + dc
            if 0 <= r < height and 0 <= c < width and out[r][c] == 0:
                out[r][c] = color

    return out
