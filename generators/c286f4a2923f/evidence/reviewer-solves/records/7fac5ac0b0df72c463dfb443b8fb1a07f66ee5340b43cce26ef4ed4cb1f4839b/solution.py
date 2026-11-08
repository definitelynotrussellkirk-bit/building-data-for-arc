from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy the red (2) shape into the green (3) frame's top-left, in cyan (8)."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    if not red or not green:
        return out

    red_top = min(r for r, _ in red)
    red_left = min(c for _, c in red)
    green_top = min(r for r, _ in green)
    green_left = min(c for _, c in green)

    for r, c in red:
        target_r = green_top + (r - red_top)
        target_c = green_left + (c - red_left)
        if 0 <= target_r < height and 0 <= target_c < width:
            out[target_r][target_c] = 8

    return out
