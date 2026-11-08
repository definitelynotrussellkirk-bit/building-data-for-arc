from __future__ import annotations


def _normalized_cells(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    if not cells:
        raise ValueError(f"missing shape color {color}")
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Combine the independently normalized color-1 and color-2 masks.

    A single corner legend cell selects the set operation:
    3 = union, 4 = intersection, 6 = symmetric difference.
    The resulting mask is rendered in color 8 in its tight bounding box.
    """
    controls = [value for row in grid for value in row if value in {3, 4, 6}]
    if len(controls) != 1:
        raise ValueError(f"expected one legend cell, found {len(controls)}")

    mask1 = _normalized_cells(grid, 1)
    mask2 = _normalized_cells(grid, 2)
    control = controls[0]
    if control == 3:
        result = mask1 | mask2
    elif control == 4:
        result = mask1 & mask2
    else:
        result = mask1 ^ mask2

    if not result:
        return [[0]]
    height = max(r for r, _ in result) + 1
    width = max(c for _, c in result) + 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in result:
        output[r][c] = 8
    return output
