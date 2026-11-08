"""Visible-example inference: place the XOR of normalized shapes at the marker."""


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    def positions(color):
        return {
            (row, column)
            for row, values in enumerate(grid)
            for column, value in enumerate(values)
            if value == color
        }

    def normalize(points):
        if not points:
            return set()
        top = min(row for row, _ in points)
        left = min(column for _, column in points)
        return {(row - top, column - left) for row, column in points}

    anchor_row, anchor_column = next(iter(positions(1)))
    red = normalize(positions(2))
    green = normalize(positions(3))
    for row, column in red ^ green:
        target_row = anchor_row + row
        target_column = anchor_column + column
        if 0 <= target_row < height and 0 <= target_column < width:
            output[target_row][target_column] = 8
    return output
