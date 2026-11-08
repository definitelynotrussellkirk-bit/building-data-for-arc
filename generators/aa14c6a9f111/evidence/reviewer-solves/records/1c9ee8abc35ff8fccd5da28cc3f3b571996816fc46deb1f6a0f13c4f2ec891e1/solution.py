from collections import defaultdict


def solve(grid):
    """Complete each nonzero color into its axis-aligned bounding-box outline."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    positions = defaultdict(list)
    color_order = []
    seen = set()
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color == 0:
                continue
            positions[color].append((row, col))
            if color not in seen:
                seen.add(color)
                color_order.append(color)

    for color in color_order:
        cells = positions[color]
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)

        for col in range(left, right + 1):
            output[top][col] = color
            output[bottom][col] = color
        for row in range(top, bottom + 1):
            output[row][left] = color
            output[row][right] = color

    return output
