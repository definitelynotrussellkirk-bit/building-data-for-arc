from copy import deepcopy


def solve(grid):
    """Stamp the framed color-4 stencil at every color-7 marker in color 8."""
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    output = deepcopy(grid)

    frame_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    if not frame_cells:
        return output

    top = min(r for r, _ in frame_cells)
    bottom = max(r for r, _ in frame_cells)
    left = min(c for _, c in frame_cells)
    right = max(c for _, c in frame_cells)

    stencil = [
        (r - (top + 1), c - (left + 1))
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] == 4
    ]
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 7
    ]

    for r, c in markers:
        output[r][c] = 0

    for anchor_r, anchor_c in markers:
        for dr, dc in stencil:
            r = anchor_r + dr
            c = anchor_c + dc
            if 0 <= r < rows and 0 <= c < cols:
                output[r][c] = 8

    return output
