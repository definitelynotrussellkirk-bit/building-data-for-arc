"""Visible-example solution for ARC task 5dc10de63325."""


def solve(grid):
    """Count cyan cells and encode count//4 in four repeated 2x2 glyphs."""
    count = sum(value == 8 for row in grid for value in row)
    filled = max(0, min(4, count // 4))

    order = ((1, 1), (1, 0), (0, 1), (0, 0))
    tile = [[0, 0], [0, 0]]
    for row, col in order[:filled]:
        tile[row][col] = 8

    output = [[0 for _ in range(5)] for _ in range(5)]
    for row_offset in (0, 3):
        for col_offset in (0, 3):
            for row in range(2):
                for col in range(2):
                    output[row_offset + row][col_offset + col] = tile[row][col]
    return output
