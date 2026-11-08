"""Visible-example solution for the generated ARC lesson."""


def solve(grid):
    """Extend each colored seed to its nearest border.

    Equal-distance borders use the order top, bottom, left, right, as
    distinguished by the visible training examples.  The seed cell is part of
    the extension.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]

    # Read seeds from the original grid so painting never creates new seeds.
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color == 0:
                continue

            distances = (
                row_index,                    # top
                height - 1 - row_index,       # bottom
                column_index,                 # left
                width - 1 - column_index,     # right
            )
            direction = min(range(4), key=lambda index: (distances[index], index))

            if direction == 0:
                cells = ((r, column_index) for r in range(row_index + 1))
            elif direction == 1:
                cells = ((r, column_index) for r in range(row_index, height))
            elif direction == 2:
                cells = ((row_index, c) for c in range(column_index + 1))
            else:
                cells = ((row_index, c) for c in range(column_index, width))

            for r, c in cells:
                output[r][c] = color

    return output
