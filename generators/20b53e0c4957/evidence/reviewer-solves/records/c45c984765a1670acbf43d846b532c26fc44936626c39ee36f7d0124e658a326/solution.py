"""Visible-example solution for the post-repair ARC episode."""


def _occupied(panel):
    return {
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    }


def _origin(cells):
    if not cells:
        raise ValueError("expected a nonempty object")
    return min(r for r, _ in cells), min(c for _, c in cells)


def solve(grid):
    """Replay the A→B cutouts, bbox-relative, on the object in panel C."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    divider_columns = [
        c
        for c in range(width)
        if all(grid[r][c] == 5 for r in range(height))
    ]
    if len(divider_columns) != 2:
        raise ValueError("expected exactly two full-height color-5 dividers")

    d1, d2 = divider_columns
    a = [row[:d1] for row in grid]
    b = [row[d1 + 1 : d2] for row in grid]
    c_panel = [row[d2 + 1 :] for row in grid]

    cells_a = _occupied(a)
    cells_b = _occupied(b)
    cells_c = _occupied(c_panel)
    a_top, a_left = _origin(cells_a)
    c_top, c_left = _origin(cells_c)

    removed_offsets = {
        (r - a_top, col - a_left)
        for r, col in cells_a - cells_b
    }

    out = [row[:] for row in c_panel]
    for dr, dc in removed_offsets:
        r, col = c_top + dr, c_left + dc
        if 0 <= r < len(out) and 0 <= col < len(out[0]):
            out[r][col] = 0
    return out
