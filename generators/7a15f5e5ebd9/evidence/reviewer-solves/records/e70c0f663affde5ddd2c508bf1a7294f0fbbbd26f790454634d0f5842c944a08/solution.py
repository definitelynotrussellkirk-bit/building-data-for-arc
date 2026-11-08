from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy the 4-cell template around every 2, using the lone 9 as origin.

    The source template (the 9 and its surrounding 4s) is only a legend, so the
    output starts from the background.  Copies are clipped to the grid, and all
    2 markers are restored last so a copied 4 never hides another destination.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(anchors) != 1:
        raise ValueError("expected exactly one color-9 template origin")
    anchor_r, anchor_c = anchors[0]

    offsets = [
        (r - anchor_r, c - anchor_c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    ]
    destinations = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]

    output = [[0 for _ in range(width)] for _ in range(height)]
    for dest_r, dest_c in destinations:
        for dr, dc in offsets:
            r, c = dest_r + dr, dest_c + dc
            if 0 <= r < height and 0 <= c < width:
                output[r][c] = 4

    for r, c in destinations:
        output[r][c] = 2
    return output
