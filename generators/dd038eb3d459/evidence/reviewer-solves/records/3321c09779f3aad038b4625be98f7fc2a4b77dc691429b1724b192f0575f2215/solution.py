from __future__ import annotations


def _mask_bbox(grid: list[list[int]], color: int) -> list[list[int]]:
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    if not cells:
        return []

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [
        [1 if grid[r][c] == color else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _rotate_clockwise(mask: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*mask[::-1])]


def _rotate_180(mask: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in mask[::-1]]


def _rotate_counterclockwise(mask: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*mask)][::-1]


def _crop_nonzero(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Rotate color 3 by the blue-corner code, then XOR it with color 2."""
    height = len(grid)
    width = len(grid[0])
    marker = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    )

    color3 = _mask_bbox(grid, 3)
    color2 = _mask_bbox(grid, 2)

    if marker == (0, 0):
        rotated3 = color3
    elif marker == (0, width - 1):
        rotated3 = _rotate_clockwise(color3)
    elif marker == (height - 1, width - 1):
        rotated3 = _rotate_180(color3)
    elif marker == (height - 1, 0):
        rotated3 = _rotate_counterclockwise(color3)
    else:
        raise ValueError("color-1 marker must occupy a grid corner")

    out_height = max(len(rotated3), len(color2))
    out_width = max(len(rotated3[0]), len(color2[0]))
    output = [[0 for _ in range(out_width)] for _ in range(out_height)]

    for r in range(out_height):
        for c in range(out_width):
            in3 = r < len(rotated3) and c < len(rotated3[0]) and rotated3[r][c]
            in2 = r < len(color2) and c < len(color2[0]) and color2[r][c]
            output[r][c] = 8 if bool(in3) ^ bool(in2) else 0

    return _crop_nonzero(output)
