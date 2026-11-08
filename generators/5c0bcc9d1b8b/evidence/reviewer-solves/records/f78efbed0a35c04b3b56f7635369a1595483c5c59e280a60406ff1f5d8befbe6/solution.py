"""Visible-example solution for ARC task 5c0bcc9d1b8b."""


def solve(grid):
    """Compress the gray motif to a centered same-count line in the track."""
    height = len(grid)
    width = len(grid[0])
    gray_count = sum(value == 5 for row in grid for value in row)

    def is_divider(values):
        return all(value in (0, 5) for value in values) or values.count(0) > len(values) // 2

    divider_cols = [
        col
        for col in range(width)
        if is_divider([grid[row][col] for row in range(height)])
    ]
    vertical_track = len(divider_cols) >= 2

    center_row = height // 2
    center_col = width // 2
    output = [[7 for _ in range(width)] for _ in range(height)]

    if vertical_track:
        for row in range(height):
            output[row][center_col - 1] = 0
            output[row][center_col + 1] = 0
        for col in range(width):
            output[center_row][col] = 0
        start = center_row - gray_count // 2
        for row in range(start, start + gray_count):
            output[row][center_col] = 5
    else:
        for col in range(width):
            output[center_row - 1][col] = 0
            output[center_row + 1][col] = 0
        for row in range(height):
            output[row][center_col] = 0
        start = center_col - gray_count // 2
        for col in range(start, start + gray_count):
            output[center_row][col] = 5

    return output
