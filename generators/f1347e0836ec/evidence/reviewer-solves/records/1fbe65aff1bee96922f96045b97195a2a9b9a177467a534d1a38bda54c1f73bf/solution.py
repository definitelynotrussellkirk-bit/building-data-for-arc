from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Paint the dot column and route its two boundary arms to opposite sides."""
    height = len(grid)
    width = len(grid[0])
    background = grid[0][0]

    dot_row = dot_col = -1
    for row in range(height):
        for col in range(width):
            if grid[row][col] != background:
                dot_row, dot_col = row, col
                break
        if dot_row >= 0:
            break
    if dot_row < 0:
        raise ValueError("expected one non-background dot")

    out = [row[:] for row in grid]
    for row in range(height):
        if row != dot_row:
            out[row][dot_col] = 1

    if dot_row == dot_col:
        top_target = width - 1
        bottom_target = 0
    else:
        top_target = 0
        bottom_target = width - 1

    for col in range(min(dot_col, top_target), max(dot_col, top_target) + 1):
        out[0][col] = 1
    for col in range(min(dot_col, bottom_target), max(dot_col, bottom_target) + 1):
        out[height - 1][col] = 1

    return out
