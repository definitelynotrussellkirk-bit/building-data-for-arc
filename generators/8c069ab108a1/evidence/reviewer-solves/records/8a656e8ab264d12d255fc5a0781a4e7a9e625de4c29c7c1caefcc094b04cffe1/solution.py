from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    anchors = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    if len(anchors) != 1:
        return [list(row) for row in grid]
    anchor_row, anchor_col = anchors[0]
    output = [[0] * width for _ in range(height)]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (0, 9):
                continue
            delta_row = row - anchor_row
            delta_col = col - anchor_col
            for _ in range(4):
                out_row = anchor_row + delta_row
                out_col = anchor_col + delta_col
                if 0 <= out_row < height and 0 <= out_col < width:
                    output[out_row][out_col] = value
                delta_row, delta_col = delta_col, -delta_row
    return output
