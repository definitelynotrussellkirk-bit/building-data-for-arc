"""Visible-example learner solution for task 329d82eaaa63."""


def solve(grid):
    """Repeat top-row seeds: straight on even rows, split left/right on odd rows."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seeds = [(column, color) for column, color in enumerate(grid[0]) if color != 0]

    for row in range(height):
        for column, color in seeds:
            if row % 2 == 0:
                output[row][column] = color
            else:
                if column > 0:
                    output[row][column - 1] = color
                if column + 1 < width:
                    output[row][column + 1] = color
    return output
