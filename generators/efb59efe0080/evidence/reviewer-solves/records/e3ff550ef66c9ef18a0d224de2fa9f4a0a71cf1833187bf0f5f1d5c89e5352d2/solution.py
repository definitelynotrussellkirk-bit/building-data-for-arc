from __future__ import annotations


def _normalized_mask(grid: list[list[int]], color: int) -> list[list[bool]]:
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
    mask = [[False] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        mask[r - r0][c - c0] = True
    return mask


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Top-left align the red and green silhouettes, XOR them, and crop."""
    masks = [_normalized_mask(grid, color) for color in (2, 3)]
    height = max((len(mask) for mask in masks), default=0)
    width = max(
        (len(row) for mask in masks for row in mask),
        default=0,
    )

    xor = [[0] * width for _ in range(height)]
    for r in range(height):
        for c in range(width):
            occupied = 0
            for mask in masks:
                if r < len(mask) and c < len(mask[r]) and mask[r][c]:
                    occupied += 1
            if occupied == 1:
                xor[r][c] = 8

    nonzero = [
        (r, c)
        for r, row in enumerate(xor)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not nonzero:
        return [[0]]

    r0 = min(r for r, _ in nonzero)
    r1 = max(r for r, _ in nonzero)
    c0 = min(c for _, c in nonzero)
    c1 = max(c for _, c in nonzero)
    return [row[c0 : c1 + 1] for row in xor[r0 : r1 + 1]]
