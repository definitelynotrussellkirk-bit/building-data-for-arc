from collections import defaultdict


def solve(grid):
    """Complete each color's four marked rectangle corners into its outline."""
    result = [row[:] for row in grid]
    cells_by_color = defaultdict(list)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                cells_by_color[color].append((row, col))

    for color, cells in cells_by_color.items():
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)

        for col in range(left, right + 1):
            if result[top][col] == 0:
                result[top][col] = color
            if result[bottom][col] == 0:
                result[bottom][col] = color
        for row in range(top, bottom + 1):
            if result[row][left] == 0:
                result[row][left] = color
            if result[row][right] == 0:
                result[row][right] = color

    return result
