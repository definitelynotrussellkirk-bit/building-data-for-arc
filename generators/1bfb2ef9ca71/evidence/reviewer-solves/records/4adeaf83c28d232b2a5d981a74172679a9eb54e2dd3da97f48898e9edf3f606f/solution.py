from __future__ import annotations


def solve(grid):
    """Draw the hollow rectangle whose opposite corners share each color."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    positions = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                positions.setdefault(color, []).append((row, col))

    for color, points in positions.items():
        if len(points) != 2:
            continue
        (row_a, col_a), (row_b, col_b) = points
        if row_a == row_b or col_a == col_b:
            continue
        top, bottom = sorted((row_a, row_b))
        left, right = sorted((col_a, col_b))
        for col in range(left, right + 1):
            output[top][col] = color
            output[bottom][col] = color
        for row in range(top, bottom + 1):
            output[row][left] = color
            output[row][right] = color
    return output
