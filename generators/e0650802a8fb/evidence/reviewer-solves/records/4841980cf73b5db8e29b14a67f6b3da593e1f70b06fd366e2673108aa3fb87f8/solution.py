def solve(grid):
    """Complete diagonal segments joining exactly two equal nonzero cells.

    Colors are processed by the row-major position of their first occurrence;
    consequently, a later segment owns any crossing cell.
    """
    output = [row[:] for row in grid]
    positions = {}

    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append((row_index, column_index))

    for color, cells in positions.items():
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = cells
        dr = r1 - r0
        dc = c1 - c0
        if abs(dr) != abs(dc):
            continue

        row_step = 1 if dr > 0 else -1
        column_step = 1 if dc > 0 else -1
        for offset in range(abs(dr) + 1):
            output[r0 + offset * row_step][c0 + offset * column_step] = color

    return output
