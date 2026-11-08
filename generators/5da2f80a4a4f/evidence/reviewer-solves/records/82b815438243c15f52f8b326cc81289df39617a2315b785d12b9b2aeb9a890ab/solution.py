from __future__ import annotations


def solve(grid):
    """Extract the colored key inside the red frame and enlarge it to fill."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a nonempty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    frame_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if not frame_cells:
        raise ValueError("no color-2 frame")
    r0 = min(r for r, _ in frame_cells)
    r1 = max(r for r, _ in frame_cells)
    c0 = min(c for _, c in frame_cells)
    c1 = max(c for _, c in frame_cells)

    key_cells = [
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] not in (0, 2)
    ]
    if not key_cells:
        raise ValueError("no colored key inside frame")
    kr0 = min(r for r, _ in key_cells)
    kr1 = max(r for r, _ in key_cells)
    kc0 = min(c for _, c in key_cells)
    kc1 = max(c for _, c in key_cells)
    key = [row[kc0 : kc1 + 1] for row in grid[kr0 : kr1 + 1]]

    out_h = r1 - r0 + 1
    out_w = c1 - c0 + 1
    inner_h = out_h - 2
    inner_w = out_w - 2
    key_h = len(key)
    key_w = len(key[0])
    if inner_h % key_h or inner_w % key_w:
        raise ValueError("key dimensions do not tile frame interior")
    row_scale = inner_h // key_h
    col_scale = inner_w // key_w

    output = [[2] * out_w]
    for key_row in key:
        expanded = [value for value in key_row for _ in range(col_scale)]
        for _ in range(row_scale):
            output.append([2, *expanded, 2])
    output.append([2] * out_w)
    return output
