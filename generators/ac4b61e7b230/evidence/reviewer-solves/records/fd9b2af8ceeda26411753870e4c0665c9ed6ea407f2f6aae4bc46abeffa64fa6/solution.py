"""Visible-only solution for blind task ac4b61e7b230."""


def solve(grid):
    """Slide the red (2) object toward the azure (8) object until collision.

    The motion is one of the eight compass directions.  On an axis where the
    two bounding boxes already overlap there is no motion; otherwise the red
    object moves one cell per step toward the azure bounding box.  The final
    position is the last non-overlapping position (the next step would collide
    with an azure cell).
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    red = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    azure = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    if not red or not azure:
        return out

    red_rows = [r for r, _ in red]
    red_cols = [c for _, c in red]
    azure_rows = [r for r, _ in azure]
    azure_cols = [c for _, c in azure]

    red_top, red_bottom = min(red_rows), max(red_rows)
    red_left, red_right = min(red_cols), max(red_cols)
    azure_top, azure_bottom = min(azure_rows), max(azure_rows)
    azure_left, azure_right = min(azure_cols), max(azure_cols)

    if red_bottom < azure_top:
        dr = 1
    elif red_top > azure_bottom:
        dr = -1
    else:
        dr = 0

    if red_right < azure_left:
        dc = 1
    elif red_left > azure_right:
        dc = -1
    else:
        dc = 0

    # Degenerate overlap is outside the observed task distribution.
    if dr == 0 and dc == 0:
        return out

    current = red
    while True:
        candidate = {(r + dr, c + dc) for r, c in current}
        if any(r < 0 or r >= height or c < 0 or c >= width for r, c in candidate):
            break
        if candidate & azure:
            break
        current = candidate

    for r, c in red:
        out[r][c] = 0
    for r, c in current:
        out[r][c] = 2
    return out
