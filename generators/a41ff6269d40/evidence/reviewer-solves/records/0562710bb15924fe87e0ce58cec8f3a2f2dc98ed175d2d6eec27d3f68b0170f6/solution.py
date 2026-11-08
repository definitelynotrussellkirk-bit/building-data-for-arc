"""Visible-example solution for a41ff6269d40."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])

    template_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 4
    ]
    if not template_cells:
        return [[0 for _ in range(width)] for _ in range(height)]

    top = min(row for row, _ in template_cells)
    left = min(col for _, col in template_cells)
    template = sorted((row - top, col - left) for row, col in template_cells)
    template_height = max(row for row, _ in template) + 1
    template_width = max(col for _, col in template) + 1

    transforms = {
        1: template,
        2: [(row, template_width - 1 - col) for row, col in template],
        3: [(template_height - 1 - row, col) for row, col in template],
    }

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value not in transforms:
                continue
            for delta_row, delta_col in transforms[value]:
                target_row = row + delta_row
                target_col = col + delta_col
                if 0 <= target_row < height and 0 <= target_col < width:
                    output[target_row][target_col] = 4
    return output
