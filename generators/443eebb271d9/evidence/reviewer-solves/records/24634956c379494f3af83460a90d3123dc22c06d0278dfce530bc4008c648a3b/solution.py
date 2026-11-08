"""Visible-example solution for reviewer-authored ARC task 443eebb271d9."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    source = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 7
    ]
    if not source:
        return [list(row) for row in grid]

    row0 = min(row for row, _ in source)
    row1 = max(row for row, _ in source)
    col0 = min(col for _, col in source)
    col1 = max(col for _, col in source)
    glyph_height = row1 - row0 + 1
    glyph_width = col1 - col0 + 1
    row_step = glyph_height + 1
    col_step = glyph_width + 1
    glyph = [(row - row0, col - col0) for row, col in source]

    output = [[0 for _ in range(width)] for _ in range(height)]
    horizontal_index = 0
    while col0 + horizontal_index * col_step < width:
        tile_col = col0 + horizontal_index * col_step
        special = horizontal_index % 3 == 2
        vertical_index = 0
        while row0 + vertical_index * row_step < height:
            if vertical_index > 0 and not special:
                break
            tile_row = row0 + vertical_index * row_step
            color = 6 if special else 7
            for local_row, local_col in glyph:
                row = tile_row + local_row
                col = tile_col + local_col
                if row < height and col < width:
                    output[row][col] = color
            vertical_index += 1
        horizontal_index += 1
    return output
