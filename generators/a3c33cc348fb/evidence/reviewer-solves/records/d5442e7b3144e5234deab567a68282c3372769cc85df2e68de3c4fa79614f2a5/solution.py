from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Extend the framed rectangle leftward until its new edge reaches color 8."""
    out = [row[:] for row in grid]

    marker_positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if len(marker_positions) != 1:
        return out
    _, marker_col = marker_positions[0]

    object_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]
    if not object_cells:
        return out

    top = min(r for r, _ in object_cells)
    bottom = max(r for r, _ in object_cells)
    left = min(c for _, c in object_cells)
    right = max(c for _, c in object_cells)
    border = grid[top][left]

    interior_values = [
        grid[r][c]
        for r in range(top + 1, bottom)
        for c in range(left + 1, right)
        if grid[r][c] not in (0, border, 8)
    ]
    if not interior_values:
        return out
    interior = interior_values[0]

    # Remove the marker before drawing the enlarged frame.
    marker_row, marker_col = marker_positions[0]
    out[marker_row][marker_col] = 0

    new_left = min(marker_col, left)
    for r in range(top, bottom + 1):
        for c in range(new_left, right + 1):
            if r in (top, bottom) or c in (new_left, right):
                out[r][c] = border
            else:
                out[r][c] = interior

    return out
