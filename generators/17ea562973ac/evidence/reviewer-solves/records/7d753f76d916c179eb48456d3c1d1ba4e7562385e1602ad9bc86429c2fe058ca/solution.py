"""Visible-only solution for blind task 17ea562973ac."""


def solve(grid):
    """Replace all foreground cells with the outline of their bounding box."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [list(row) for row in grid]

    colors = {value for _, _, value in cells}
    if len(colors) != 1:
        raise ValueError("expected one nonzero foreground color")
    color = next(iter(colors))

    min_r = min(r for r, _, _ in cells)
    max_r = max(r for r, _, _ in cells)
    min_c = min(c for _, c, _ in cells)
    max_c = max(c for _, c, _ in cells)

    out = [[0 for _ in range(width)] for _ in grid]
    for c in range(min_c, max_c + 1):
        out[min_r][c] = color
        out[max_r][c] = color
    for r in range(min_r, max_r + 1):
        out[r][min_c] = color
        out[r][max_c] = color
    return out
