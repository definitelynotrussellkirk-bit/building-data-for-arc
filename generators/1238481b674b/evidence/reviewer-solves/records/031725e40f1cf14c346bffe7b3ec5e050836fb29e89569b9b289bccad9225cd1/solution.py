from __future__ import annotations

from copy import deepcopy


def solve(grid):
    """Draw the outline of the triangle whose apex is the missing bbox corner."""
    out = deepcopy(grid)
    marks = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    if len(marks) != 4:
        raise ValueError(f"expected four gray markers, found {len(marks)}")

    top = min(row for row, _ in marks)
    bottom = max(row for row, _ in marks)
    left = min(col for _, col in marks)
    right = max(col for _, col in marks)
    if bottom - top != right - left:
        raise ValueError("gray-marker bounding box is not square")

    corners = ((top, left), (top, right), (bottom, left), (bottom, right))
    missing = [index for index, corner in enumerate(corners) if corner not in marks]
    if len(missing) != 1:
        raise ValueError("expected exactly one missing bounding-box corner")
    missing = missing[0]
    side = bottom - top

    for step in range(side + 1):
        if missing == 0:  # top-left apex
            cells = (
                (top, left + step),
                (top + step, left),
                (top + step, right - step),
            )
        elif missing == 1:  # top-right apex
            cells = (
                (top, left + step),
                (top + step, right),
                (top + step, left + step),
            )
        elif missing == 2:  # bottom-left apex
            cells = (
                (bottom, left + step),
                (top + step, left),
                (top + step, left + step),
            )
        else:  # bottom-right apex
            cells = (
                (bottom, left + step),
                (top + step, right),
                (top + step, right - step),
            )
        for row, col in cells:
            if out[row][col] == 7:
                out[row][col] = 8
    return out
