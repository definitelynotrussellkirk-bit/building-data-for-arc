"""Visible-example solution for task 24d677c76640."""


def solve(grid):
    """Move the colored pattern so its bounding-box top-left lands on the 1 marker."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    if len(markers) != 1:
        raise ValueError("expected exactly one color-1 destination marker")
    dest_r, dest_c = markers[0]

    pattern = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1)
    ]
    if not pattern:
        raise ValueError("expected a non-marker colored pattern")

    src_top = min(r for r, _, _ in pattern)
    src_left = min(c for _, c, _ in pattern)

    out = [[0 for _ in range(width)] for _ in range(height)]
    for r, c, value in pattern:
        nr = dest_r + (r - src_top)
        nc = dest_c + (c - src_left)
        if not (0 <= nr < height and 0 <= nc < width):
            raise ValueError("translated pattern does not fit in the grid")
        out[nr][nc] = value
    return out
