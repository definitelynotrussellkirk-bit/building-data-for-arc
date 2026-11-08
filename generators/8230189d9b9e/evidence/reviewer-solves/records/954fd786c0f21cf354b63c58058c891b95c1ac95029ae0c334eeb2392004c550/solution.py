def solve(grid):
    """Expand the bottom-row key sequence using the labelled 3-by-3 tiles."""
    tiles = {}
    for column, key in enumerate(grid[0]):
        if key:
            tiles[key] = [row[column - 1:column + 2] for row in grid[1:4]]
    sequence = [key for key in grid[-1] if key]
    output = [[] for _ in range(3)]
    for index, key in enumerate(sequence):
        for row_index in range(3):
            if index:
                output[row_index].append(0)
            output[row_index].extend(tiles[key][row_index])
    return output
