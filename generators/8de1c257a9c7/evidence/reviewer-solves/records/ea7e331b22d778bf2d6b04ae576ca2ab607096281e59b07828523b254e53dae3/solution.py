from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Stamp the cyan template, measured from the green anchor, at every red marker."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    greens = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    ]
    reds = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    cyan = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    if len(greens) != 1:
        raise ValueError(f"expected exactly one green anchor, found {len(greens)}")

    anchor_r, anchor_c = greens[0]
    offsets = [(r - anchor_r, c - anchor_c) for r, c in cyan]
    result = [[0 for _ in range(width)] for _ in range(height)]

    for marker_r, marker_c in reds:
        for dr, dc in offsets:
            r = marker_r + dr
            c = marker_c + dc
            if 0 <= r < height and 0 <= c < width:
                result[r][c] = 8

    return result
