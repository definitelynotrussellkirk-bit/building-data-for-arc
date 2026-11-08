"""Visible-example solution for reviewer solve task 9b5d72b45563."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    offsets = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for delta_row, delta_col in offsets:
                next_row = row + delta_row
                next_col = col + delta_col
                if 0 <= next_row < height and 0 <= next_col < width:
                    output[next_row][next_col] = color
    return output
