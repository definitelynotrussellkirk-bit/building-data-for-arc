def solve(grid):
    """Project each color-1 marker one cell toward its matching solid border."""
    if not grid or not grid[0]:
        return grid

    height = len(grid)
    width = len(grid[0])

    def solid_non_marker(values):
        return bool(values) and len(set(values)) == 1 and values[0] not in (0, 1)

    horizontal = solid_non_marker(grid[0]) and solid_non_marker(grid[-1])
    left_column = [row[0] for row in grid]
    right_column = [row[-1] for row in grid]
    vertical = solid_non_marker(left_column) and solid_non_marker(right_column)
    if horizontal == vertical:
        raise ValueError("expected exactly one pair of solid opposite borders")

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    output = [row[:] for row in grid]

    if horizontal:
        first_color = grid[0][0]
        second_color = grid[-1][0]
        for row, col in markers:
            first_half = 2 * row < height
            target_row = row - 1 if first_half else row + 1
            output[target_row][col] = first_color if first_half else second_color
    else:
        first_color = grid[0][0]
        second_color = grid[0][-1]
        for row, col in markers:
            first_half = 2 * col < width
            target_col = col - 1 if first_half else col + 1
            output[row][target_col] = first_color if first_half else second_color

    return output
