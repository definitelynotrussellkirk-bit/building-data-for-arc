from collections import defaultdict


def solve(grid):
    """Fill each colored rectangular frame with a two-color checkerboard.

    The frame keeps its color.  The single non-frame color inside the frame is
    used as the checkerboard ink, with that color at the interior's top-left.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_color[value].append((r, c))

    frames = []
    for color, cells in by_color.items():
        if len(cells) < 8:
            continue
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r0, r1 = min(rows), max(rows)
        c0, c1 = min(cols), max(cols)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue

        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if all(grid[r][c] == color for r, c in perimeter):
            frames.append((r0, r1, c0, c1, color))

    for r0, r1, c0, c1, frame_color in frames:
        marker_colors = {
            grid[r][c]
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, frame_color)
        }
        if len(marker_colors) != 1:
            continue
        marker_color = next(iter(marker_colors))
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                out[r][c] = (
                    marker_color
                    if ((r - (r0 + 1)) + (c - (c0 + 1))) % 2 == 0
                    else frame_color
                )

    return out
