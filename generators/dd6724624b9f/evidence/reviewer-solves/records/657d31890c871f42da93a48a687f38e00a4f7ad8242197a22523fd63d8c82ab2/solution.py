from __future__ import annotations


def _crop_body(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row in range(1, len(grid))
        for col, value in enumerate(grid[row])
        if value != 0
    ]
    if not cells:
        raise ValueError("input has no body below the control strip")
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [
        [1 if grid[row][col] != 0 else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]


def _rotate_clockwise(mask: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*mask[::-1])]


def solve(grid):
    code = grid[0][0]
    output_color = grid[0][1]
    mask = _crop_body(grid)

    if code == 1:          # unchanged
        transformed = mask
    elif code == 2:        # mirror left/right
        transformed = [row[::-1] for row in mask]
    elif code == 3:        # mirror up/down
        transformed = mask[::-1]
    elif code == 4:        # quarter-turn clockwise
        transformed = _rotate_clockwise(mask)
    elif code == 5:        # half-turn
        transformed = [row[::-1] for row in mask[::-1]]
    elif code == 6:        # quarter-turn counterclockwise
        transformed = _rotate_clockwise(_rotate_clockwise(_rotate_clockwise(mask)))
    else:
        raise ValueError(f"unknown transform code: {code!r}")

    return [
        [output_color if value else 0 for value in row]
        for row in transformed
    ]
