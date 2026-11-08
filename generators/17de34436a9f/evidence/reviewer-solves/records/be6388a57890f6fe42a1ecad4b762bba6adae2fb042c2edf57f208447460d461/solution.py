from __future__ import annotations


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Crop the colored object and rotate it according to the corner marker.

    The gray 9 marks which corner should be treated as the object's canonical
    top-left orientation: top-left means no rotation, then each clockwise
    marker step adds one clockwise quarter-turn to the cropped object.
    """
    height = len(grid)
    width = len(grid[0])

    marker = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    )

    object_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    if not object_cells:
        return []

    r0 = min(r for r, _ in object_cells)
    r1 = max(r for r, _ in object_cells)
    c0 = min(c for _, c in object_cells)
    c1 = max(c for _, c in object_cells)
    cropped = [
        [0 if value == 9 else value for value in row[c0 : c1 + 1]]
        for row in grid[r0 : r1 + 1]
    ]

    turns_by_corner = {
        (0, 0): 0,
        (0, width - 1): 1,
        (height - 1, width - 1): 2,
        (height - 1, 0): 3,
    }
    turns = turns_by_corner[marker]
    for _ in range(turns):
        cropped = _rotate_clockwise(cropped)
    return cropped
