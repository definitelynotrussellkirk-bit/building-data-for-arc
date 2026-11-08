"""Visible-example solution for the blind ARC task."""


def solve(grid):
    """Fill the bounding box of each nonzero color that appears exactly twice.

    Any other nonzero marks are distractors and are omitted from the output.
    The output keeps the input dimensions and uses zero as the background.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    positions = {}
    for row, values in enumerate(grid):
        if len(values) != width:
            raise ValueError("grid must be rectangular")
        for column, color in enumerate(values):
            if color != 0:
                positions.setdefault(color, []).append((row, column))

    output = [[0 for _ in range(width)] for _ in range(height)]
    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (row_a, column_a), (row_b, column_b) = cells
        row_min, row_max = sorted((row_a, row_b))
        column_min, column_max = sorted((column_a, column_b))
        for row in range(row_min, row_max + 1):
            for column in range(column_min, column_max + 1):
                output[row][column] = color

    return output
