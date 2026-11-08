from __future__ import annotations


def solve(grid):
    """Pack the colored rectangles into a top-left corner-sharing staircase."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    cells_by_color = {}
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color != 0:
                cells_by_color.setdefault(color, []).append((row, column))

    rectangles = []
    for color, cells in cells_by_color.items():
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(columns), max(columns)
        rectangles.append((left, top, color, bottom - top + 1, right - left + 1))

    cursor_row = 0
    cursor_column = 0
    for _left, _top, color, rect_height, rect_width in sorted(rectangles):
        for row in range(cursor_row, cursor_row + rect_height):
            for column in range(cursor_column, cursor_column + rect_width):
                output[row][column] = color
        cursor_row += rect_height - 1
        cursor_column += rect_width - 1

    return output
