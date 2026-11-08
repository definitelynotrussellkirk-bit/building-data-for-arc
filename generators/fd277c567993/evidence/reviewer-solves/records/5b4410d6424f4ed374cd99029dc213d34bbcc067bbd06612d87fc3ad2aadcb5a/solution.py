"""Visible-example solution for the blind ARC task.

The input is three equal-width canvases separated by two one-column dividers.
Panel 2 repeats panel 1 and adds marker cells. Translate those additions by how
far panel 3's foreground bounding-box origin is from panel 1's, then draw them
over panel 3.
"""


def _bbox_origin(panel):
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        raise ValueError("expected a non-empty foreground object")
    return min(r for r, _ in cells), min(c for _, c in cells)


def solve(grid):
    if not grid or not grid[0]:
        return []

    height = len(grid)
    total_width = len(grid[0])
    if any(len(row) != total_width for row in grid):
        raise ValueError("grid must be rectangular")
    if total_width < 5 or (total_width - 2) % 3:
        raise ValueError("expected three equal panels and two dividers")

    width = (total_width - 2) // 3
    panel_1 = [row[:width] for row in grid]
    panel_2 = [row[width + 1 : 2 * width + 1] for row in grid]
    panel_3 = [row[2 * width + 2 :] for row in grid]

    src_r, src_c = _bbox_origin(panel_1)
    dst_r, dst_c = _bbox_origin(panel_3)
    dr, dc = dst_r - src_r, dst_c - src_c

    result = [row[:] for row in panel_3]
    for r in range(height):
        for c in range(width):
            value = panel_2[r][c]
            if value != 0 and value != panel_1[r][c]:
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width:
                    result[rr][cc] = value

    return result
