from collections import Counter


def solve(grid):
    """Fill the interior of the color-8 frame with the unique singleton color."""
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

    counts = Counter(value for row in grid for value in row)
    singleton_colors = [
        color for color, count in counts.items()
        if color not in (0, 8) and count == 1
    ]
    if len(singleton_colors) != 1:
        return out
    fill = singleton_colors[0]

    for r in range(top + 1, bottom):
        for c in range(left + 1, right):
            out[r][c] = fill
    return out
