def solve(grid):
    """Complete every nonzero straight adjacent pair through 3-cell windows."""
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height = len(source)
    width = len(source[0]) if height else 0

    for row in range(height):
        for col in range(width - 2):
            left, middle, right = source[row][col : col + 3]
            if left == 0 and middle != 0 and middle == right:
                output[row][col] = middle
            elif left != 0 and left == middle and right == 0:
                output[row][col + 2] = left

    for row in range(height - 2):
        for col in range(width):
            top = source[row][col]
            middle = source[row + 1][col]
            bottom = source[row + 2][col]
            if top == 0 and middle != 0 and middle == bottom:
                output[row][col] = middle
            elif top != 0 and top == middle and bottom == 0:
                output[row + 2][col] = top

    return output
