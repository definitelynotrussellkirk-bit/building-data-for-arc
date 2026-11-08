"""Visible-example solution for the prepared ARC lesson."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]

    for column in range(width):
        row = 0
        while row < height:
            color = grid[row][column]
            if color == 0:
                row += 1
                continue

            end = row + 1
            while end < height and grid[end][column] == color:
                end += 1

            if end - row == 3 and 0 < column < width - 1:
                middle = row + 1
                output[middle][column - 1] = color
                output[middle][column] = color
                output[middle][column + 1] = color

            row = end

    return output
