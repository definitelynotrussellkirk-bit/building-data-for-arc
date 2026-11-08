"""Copy the red template at each green bounding-box anchor."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    result = [[0] * width for _ in range(height)]

    template = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    if not template:
        return result

    top = min(row for row, _ in template)
    left = min(col for _, col in template)
    offsets = [(row - top, col - left) for row, col in template]

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 3:
                continue
            for delta_row, delta_col in offsets:
                target_row = row + delta_row
                target_col = col + delta_col
                if 0 <= target_row < height and 0 <= target_col < width:
                    result[target_row][target_col] = 8
    return result
