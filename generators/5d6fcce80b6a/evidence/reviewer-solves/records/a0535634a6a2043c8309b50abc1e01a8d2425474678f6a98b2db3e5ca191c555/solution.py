def solve(grid):
    """Duplicate the grid diagonally and mark nonterminal blank rows in green."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(2 * width)] for _ in range(2 * height)]

    for row_index, row in enumerate(grid):
        if len(row) != width:
            raise ValueError("grid must be rectangular")

        if row_index < height - 1 and all(value == 0 for value in row):
            output[row_index] = [3] * (2 * width)
            output[row_index + height] = [3] * (2 * width)
            continue

        for column_index, value in enumerate(row):
            output[row_index][column_index] = value
            output[row_index + height][column_index + width] = value

    return output
