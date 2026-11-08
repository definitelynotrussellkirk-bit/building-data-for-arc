def solve(grid):
    """Fill the center zero of every original horizontal a,0,a window."""
    output = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        for column in range(len(row) - 2):
            left, middle, right = row[column : column + 3]
            if left != 0 and middle == 0 and right == left:
                output[row_index][column + 1] = left
    return output
