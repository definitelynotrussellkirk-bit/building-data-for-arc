from collections import deque


def _components_of_color(grid, color):
    rows, cols = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while q:
                cr, cc = q.popleft()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            components.append(cells)
    return components


def solve(grid):
    """Copy the tight stencil rectangle into every solid gray (5) canvas."""
    out = [row[:] for row in grid]
    gray_components = _components_of_color(grid, 5)
    if not gray_components:
        return out

    boxes = []
    for cells in gray_components:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        top, bottom = min(rs), max(rs)
        left, right = min(cs), max(cs)
        boxes.append((top, left, bottom - top + 1, right - left + 1))

    # All visible examples use congruent gray canvases.  Their dimensions define
    # the containing canvases; the stencil itself is its tight colored bounding box.
    height, width = boxes[0][2], boxes[0][3]

    colored = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    if not colored:
        return out

    stencil_top = min(r for r, _ in colored)
    stencil_bottom = max(r for r, _ in colored)
    stencil_left = min(c for _, c in colored)
    stencil_right = max(c for _, c in colored)
    stencil_height = stencil_bottom - stencil_top + 1
    stencil_width = stencil_right - stencil_left + 1
    stencil = [
        grid[r][stencil_left : stencil_right + 1]
        for r in range(stencil_top, stencil_bottom + 1)
    ]

    for top, left, box_h, box_w in boxes:
        if (box_h, box_w) != (height, width):
            continue
        if stencil_height > box_h or stencil_width > box_w:
            continue
        for dr in range(stencil_height):
            for dc in range(stencil_width):
                out[top + dr][left + dc] = stencil[dr][dc]
    return out
