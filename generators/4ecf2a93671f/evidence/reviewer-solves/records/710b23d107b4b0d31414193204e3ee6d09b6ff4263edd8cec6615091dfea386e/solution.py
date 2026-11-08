from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replace every zero cell by a copy of the input's zero-mask.

    The copied mask uses the input's sole non-zero color. Non-zero input cells
    correspond to blank blocks. For an H×W input, the result is H²×W².
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    foreground = next(
        (value for row in grid for value in row if value != 0),
        0,
    )
    zero_mask = [[value == 0 for value in row] for row in grid]

    output = [[0 for _ in range(width * width)] for _ in range(height * height)]
    for outer_row in range(height):
        for outer_col in range(width):
            if not zero_mask[outer_row][outer_col]:
                continue
            row_offset = outer_row * height
            col_offset = outer_col * width
            for inner_row in range(height):
                for inner_col in range(width):
                    if zero_mask[inner_row][inner_col]:
                        output[row_offset + inner_row][col_offset + inner_col] = foreground

    return output
