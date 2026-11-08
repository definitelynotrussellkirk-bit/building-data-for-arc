def solve(grid):
    """Decode the requested 3x3 tiles and concatenate them left-to-right."""
    key_row = grid[0]
    request_row = grid[-1]

    tiles = {}
    for column, marker in enumerate(key_row):
        if marker == 0:
            continue
        tiles[marker] = [row[column - 1 : column + 2] for row in grid[1:4]]

    requested_markers = [value for value in request_row if value != 0]
    output = [[], [], []]
    for index, marker in enumerate(requested_markers):
        if index:
            for row in output:
                row.append(0)
        tile = tiles[marker]
        for row_index in range(3):
            output[row_index].extend(tile[row_index])
    return output
