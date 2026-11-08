from __future__ import annotations


def solve(grid):
    """Overlay corresponding quadrant cells with TR > BL > BR > TL priority."""
    height = len(grid)
    width = len(grid[0])
    half_h = height // 2
    half_w = width // 2
    output = [[0 for _ in range(half_w)] for _ in range(half_h)]
    for row in range(half_h):
        for col in range(half_w):
            tl = grid[row][col]
            tr = grid[row][col + half_w]
            bl = grid[row + half_h][col]
            br = grid[row + half_h][col + half_w]
            output[row][col] = next(
                (value for value in (tr, bl, br, tl) if value != 0),
                0,
            )
    return output
