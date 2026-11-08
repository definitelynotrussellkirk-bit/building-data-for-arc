def solve(grid):
    """Expand each aligned dot rectangle and draw stride-two gray guides."""
    height = len(grid)
    width = len(grid[0])
    dots = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]

    painted = {}

    # Each dot becomes the centre of a clipped 3x3 block.  The ring copies
    # the colour of the other dot in the same row.
    for row, col, colour in dots:
        row_partner = next(
            (other_colour for other_row, other_col, other_colour in dots
             if other_row == row and other_col != col),
            0,
        )
        for delta_row in (-1, 0, 1):
            for delta_col in (-1, 0, 1):
                out_row = row + delta_row
                out_col = col + delta_col
                if 0 <= out_row < height and 0 <= out_col < width:
                    painted[(out_row, out_col)] = (
                        colour if delta_row == 0 and delta_col == 0
                        else row_partner
                    )

    # Join every aligned pair by colour 5 at stride two, approaching from
    # both ends.  Guides are painted after the blocks, as in the examples.
    for first_index, (row1, col1, _colour1) in enumerate(dots):
        for row2, col2, _colour2 in dots[first_index + 1:]:
            if row1 == row2:
                left, right = sorted((col1, col2))
                midpoint = (left + right) / 2
                col = left + 2
                while col <= midpoint:
                    painted[(row1, col)] = 5
                    col += 2
                col = right - 2
                while col >= midpoint:
                    painted[(row1, col)] = 5
                    col -= 2
            if col1 == col2:
                top, bottom = sorted((row1, row2))
                midpoint = (top + bottom) / 2
                row = top + 2
                while row <= midpoint:
                    painted[(row, col1)] = 5
                    row += 2
                row = bottom - 2
                while row >= midpoint:
                    painted[(row, col1)] = 5
                    row -= 2

    return [
        [painted.get((row, col), 0) for col in range(width)]
        for row in range(height)
    ]
