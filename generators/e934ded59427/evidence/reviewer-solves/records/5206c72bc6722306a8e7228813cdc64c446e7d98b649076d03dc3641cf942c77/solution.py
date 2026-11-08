from collections import defaultdict


def solve(grid):
    """Complete each same-colored pair into its axis-aligned rectangle border."""
    output = [row[:] for row in grid]
    positions = defaultdict(list)

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, column_index))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue

        (row_a, column_a), (row_b, column_b) = cells
        top, bottom = sorted((row_a, row_b))
        left, right = sorted((column_a, column_b))

        for column in range(left, right + 1):
            output[top][column] = color
            output[bottom][column] = color
        for row in range(top, bottom + 1):
            output[row][left] = color
            output[row][right] = color

    return output
