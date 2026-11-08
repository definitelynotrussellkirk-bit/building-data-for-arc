def solve(grid):
    """Render nearby color-8 cells in the coordinate frame encoded by 2/3/4.

    Color 2 is the frame origin.  The vector from 2 to 4 is the output-row
    direction, and the vector from 2 to 3 is the output-column direction.
    Only color-8 cells whose local row and column are both in [-1, 1] appear
    in the returned 3x3 grid.
    """
    positions = {}
    eights = []
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            if value in (2, 3, 4):
                positions[value] = (row_index, column_index)
            elif value == 8:
                eights.append((row_index, column_index))

    if set(positions) != {2, 3, 4}:
        raise ValueError("grid must contain exactly one frame marker of colors 2, 3, and 4")

    origin_row, origin_column = positions[2]
    row_vector = (
        positions[4][0] - origin_row,
        positions[4][1] - origin_column,
    )
    column_vector = (
        positions[3][0] - origin_row,
        positions[3][1] - origin_column,
    )

    # [dr, dc] = local_row * row_vector + local_col * column_vector.
    determinant = (
        row_vector[0] * column_vector[1]
        - column_vector[0] * row_vector[1]
    )
    if determinant == 0:
        raise ValueError("frame markers 2, 3, and 4 must define two independent directions")

    output = [[0, 0, 0] for _ in range(3)]
    for row_index, column_index in eights:
        delta_row = row_index - origin_row
        delta_column = column_index - origin_column
        local_row_numerator = (
            delta_row * column_vector[1]
            - column_vector[0] * delta_column
        )
        local_column_numerator = (
            row_vector[0] * delta_column
            - delta_row * row_vector[1]
        )
        if (
            local_row_numerator % determinant != 0
            or local_column_numerator % determinant != 0
        ):
            continue
        local_row = local_row_numerator // determinant
        local_column = local_column_numerator // determinant
        if -1 <= local_row <= 1 and -1 <= local_column <= 1:
            output[local_row + 1][local_column + 1] = 8

    return output
