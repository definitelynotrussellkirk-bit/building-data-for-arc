"""Visible-example solution for task 64758b03899f."""


def solve(grid):
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    mask = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    output = [[0 for _ in range(width)] for _ in range(height)]
    if not mask:
        return output

    top = min(row for row, _ in mask)
    left = min(col for _, col in mask)
    offsets = [(row - top, col - left) for row, col in mask]

    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color in (0, 5):
                continue
            for d_row, d_col in offsets:
                out_row = row + d_row
                out_col = col + d_col
                if 0 <= out_row < height and 0 <= out_col < width:
                    output[out_row][out_col] = color
    return output
