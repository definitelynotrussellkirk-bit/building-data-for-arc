def solve(grid):
    """Recombine the neighboring colors and heights of bottom-aligned bars."""
    height = len(grid)
    width = len(grid[0])
    background = 7
    bar_columns = [
        column
        for column in range(width)
        if any(row[column] != background for row in grid)
    ]
    if not bar_columns:
        return [list(row) for row in grid]

    colors = [grid[-1][column] for column in bar_columns]
    heights = [
        sum(row[column] != background for row in grid)
        for column in bar_columns
    ]
    target_colors = colors[-1:] + colors[:-1]
    target_heights = heights[1:] + heights[:1]

    output = [[background for _ in range(width)] for _ in range(height)]
    for column, color, bar_height in zip(bar_columns, target_colors, target_heights):
        for row in range(height - bar_height, height):
            output[row][column] = color
    return output
