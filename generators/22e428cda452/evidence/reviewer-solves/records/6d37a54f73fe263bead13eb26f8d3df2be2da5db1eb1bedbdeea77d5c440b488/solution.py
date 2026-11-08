def solve(grid):
    """Project colored corner markers inward using the visible side-specific glyphs."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    corners = ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1))
    markers = [(row, col, grid[row][col]) for row, col in corners if grid[row][col] != 7]

    for row, col, _ in markers:
        output[row][col] = 7

    square_offsets = ((1, 1), (1, 2), (2, 1), (2, 2))
    bent_offsets = ((3, 2), (2, 2), (1, 3))
    for row, col, color in markers:
        top = row == 0
        left = col == 0
        row_sign = 1 if top else -1
        col_sign = 1 if left else -1
        offsets = square_offsets if top else bent_offsets
        for row_offset, col_offset in offsets:
            output[row + row_sign * row_offset][col + col_sign * col_offset] = color

    return output
