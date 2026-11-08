"""Visible-example solution for f1668de79fa1."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    template = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    anchors = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]
    if not template or len(anchors) != 1:
        raise ValueError("expected a nonempty color-2 template and one color-1 anchor")

    top = min(row for row, _ in template)
    left = min(col for _, col in template)
    right = max(col for _, col in template)
    normalized = [(row - top, col - left) for row, col in template]
    box_width = right - left + 1

    anchor_row, anchor_col = anchors[0]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for drow, dcol in normalized:
        out_row = anchor_row + drow
        out_col = anchor_col + (box_width - 1 - dcol)
        if 0 <= out_row < height and 0 <= out_col < width:
            output[out_row][out_col] = 8
    return output
