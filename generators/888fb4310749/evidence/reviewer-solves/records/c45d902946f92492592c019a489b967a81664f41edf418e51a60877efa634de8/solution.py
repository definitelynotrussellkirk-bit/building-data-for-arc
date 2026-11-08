from copy import deepcopy


def solve(grid):
    """Roll the lone solid rectangle along all four diagonals.

    Each roll swaps the rectangle's height and width.  Odd rolls use the
    complementary ARC colour ``9 - source_colour`` and even rolls restore the
    source colour.  Rectangles are clipped at the canvas boundary.
    """
    if not grid or not grid[0]:
        return deepcopy(grid)

    height = len(grid)
    width = len(grid[0])
    coloured = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not coloured:
        return deepcopy(grid)

    row0 = min(row for row, _ in coloured)
    row1 = max(row for row, _ in coloured)
    col0 = min(col for _, col in coloured)
    col1 = max(col for _, col in coloured)
    source_colour = grid[coloured[0][0]][coloured[0][1]]
    alternate_colour = 9 - source_colour

    result = deepcopy(grid)

    for vertical_direction in (-1, 1):
        for horizontal_direction in (-1, 1):
            current_row0, current_row1 = row0, row1
            current_col0, current_col1 = col0, col1
            step = 0

            while True:
                step += 1
                current_height = current_row1 - current_row0 + 1
                current_width = current_col1 - current_col0 + 1
                next_height = current_width
                next_width = current_height

                if vertical_direction < 0:
                    next_row1 = current_row0 - 1
                    next_row0 = next_row1 - next_height + 1
                else:
                    next_row0 = current_row1 + 1
                    next_row1 = next_row0 + next_height - 1

                if horizontal_direction < 0:
                    next_col1 = current_col0 - 1
                    next_col0 = next_col1 - next_width + 1
                else:
                    next_col0 = current_col1 + 1
                    next_col1 = next_col0 + next_width - 1

                visible_row0 = max(0, next_row0)
                visible_row1 = min(height - 1, next_row1)
                visible_col0 = max(0, next_col0)
                visible_col1 = min(width - 1, next_col1)

                if visible_row0 > visible_row1 or visible_col0 > visible_col1:
                    break

                colour = alternate_colour if step % 2 else source_colour
                for row in range(visible_row0, visible_row1 + 1):
                    for col in range(visible_col0, visible_col1 + 1):
                        result[row][col] = colour

                current_row0, current_row1 = next_row0, next_row1
                current_col0, current_col1 = next_col0, next_col1

    return result
