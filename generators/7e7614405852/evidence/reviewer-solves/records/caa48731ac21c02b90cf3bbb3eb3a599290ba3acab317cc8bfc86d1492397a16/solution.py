def solve(grid):
    """Recolor the center of each maximal horizontal nonzero run of length 3."""
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        col = 0
        while col < len(row):
            color = row[col]
            if color == 0:
                col += 1
                continue
            stop = col + 1
            while stop < len(row) and row[stop] == color:
                stop += 1
            if stop - col == 3:
                output[row_index][col + 1] = 8
            col = stop
    return output
