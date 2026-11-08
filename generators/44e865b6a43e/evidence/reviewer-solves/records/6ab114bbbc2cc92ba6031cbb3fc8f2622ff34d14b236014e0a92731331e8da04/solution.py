from collections import Counter


def solve(grid):
    """Rotate bar colors right and bar heights left across active columns."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]

    columns = []
    colors = []
    lengths = []
    for col in range(width):
        cells = [grid[row][col] for row in range(height) if grid[row][col] != background]
        if not cells:
            continue
        columns.append(col)
        colors.append(Counter(cells).most_common(1)[0][0])
        lengths.append(len(cells))

    if not columns:
        return [row[:] for row in grid]

    result = [[background for _ in range(width)] for _ in range(height)]
    count = len(columns)
    for index, col in enumerate(columns):
        out_color = colors[(index - 1) % count]
        out_length = lengths[(index + 1) % count]
        for row in range(height - out_length, height):
            result[row][col] = out_color
    return result
