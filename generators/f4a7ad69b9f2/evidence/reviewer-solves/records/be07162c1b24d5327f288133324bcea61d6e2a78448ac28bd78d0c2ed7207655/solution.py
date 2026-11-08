def solve(grid):
    """Crop each colored object, order the crops, and pack them left-to-right."""
    colors = sorted({value for row in grid for value in row if value != 0})
    pieces = []

    for color in colors:
        cells = [
            (row_index, column_index)
            for row_index, row in enumerate(grid)
            for column_index, value in enumerate(row)
            if value == color
        ]
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(column for _, column in cells)
        right = max(column for _, column in cells)

        crop = [
            [color if grid[row][column] == color else 0
             for column in range(left, right + 1)]
            for row in range(top, bottom + 1)
        ]
        mask = tuple(tuple(value != 0 for value in row) for row in crop)
        height = len(crop)
        width = len(crop[0])
        pieces.append((width, height, mask, color, crop))

    # Every visible example orders by increasing crop width, then height.  The
    # binary crop itself resolves equal-size but differently shaped pieces; the
    # color is the only visible discriminator for identical shapes.
    pieces.sort(key=lambda piece: piece[:4])

    output_height = max(height for _, height, _, _, _ in pieces)
    output_width = sum(width for width, _, _, _, _ in pieces) + len(pieces) - 1
    output = [[0] * output_width for _ in range(output_height)]

    output_column = 0
    for width, height, _, _, crop in pieces:
        for row in range(height):
            output[row][output_column:output_column + width] = crop[row]
        output_column += width + 1

    return output
