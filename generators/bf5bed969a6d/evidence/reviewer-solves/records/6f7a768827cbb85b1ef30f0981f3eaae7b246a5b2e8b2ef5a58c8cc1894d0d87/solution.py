from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Erase the red stencil and center a same-shape copy inside each frame.

    The visible tasks use color 2 as a small stencil and every other non-zero
    color as the outline of a rectangular frame.  A stencil copy is drawn in
    the frame's own color, centered in its interior.  Existing non-background
    cells are preserved, so intersecting frame outlines remain intact.
    """
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    stencil_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if out[row][col] == 2
    ]
    if not stencil_cells:
        return out

    stencil_top = min(row for row, _ in stencil_cells)
    stencil_left = min(col for _, col in stencil_cells)
    stencil_bottom = max(row for row, _ in stencil_cells)
    stencil_right = max(col for _, col in stencil_cells)
    stencil_height = stencil_bottom - stencil_top + 1
    stencil_width = stencil_right - stencil_left + 1
    stencil = {
        (row - stencil_top, col - stencil_left)
        for row, col in stencil_cells
    }

    for row, col in stencil_cells:
        out[row][col] = 0

    frame_colors = sorted(
        {
            value
            for row in grid
            for value in row
            if value not in (0, 2)
        }
    )
    for color in frame_colors:
        cells = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        ]
        if not cells:
            continue

        top = min(row for row, _ in cells)
        left = min(col for _, col in cells)
        bottom = max(row for row, _ in cells)
        right = max(col for _, col in cells)
        interior_height = bottom - top - 1
        interior_width = right - left - 1
        if interior_height < stencil_height or interior_width < stencil_width:
            continue

        stamp_top = top + 1 + (interior_height - stencil_height) // 2
        stamp_left = left + 1 + (interior_width - stencil_width) // 2
        for dr, dc in stencil:
            row = stamp_top + dr
            col = stamp_left + dc
            if out[row][col] == 0:
                out[row][col] = color

    return out
