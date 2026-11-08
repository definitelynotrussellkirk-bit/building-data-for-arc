from collections import defaultdict


def solve(grid):
    """Complete rectangle borders for colors that occur exactly twice.

    Colors are processed by the row-major position of their first occurrence;
    therefore later-starting rectangles overwrite earlier borders at crossings.
    All other cells are preserved unless a rectangle border covers them.
    """
    positions = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    ordered_colors = sorted(
        (color for color, cells in positions.items() if len(cells) == 2),
        key=lambda color: positions[color][0],
    )

    result = [row[:] for row in grid]
    for color in ordered_colors:
        (r1, c1), (r2, c2) = positions[color]
        top, bottom = sorted((r1, r2))
        left, right = sorted((c1, c2))

        for column in range(left, right + 1):
            result[top][column] = color
            result[bottom][column] = color
        for row in range(top, bottom + 1):
            result[row][left] = color
            result[row][right] = color

    return result
