def solve(grid):
    """Expand the vertical 7-source into the visible alternating triangle."""
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    sevens = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 7
    ]
    if not sevens:
        raise ValueError("input has no color-7 source")

    source_col = sevens[0][1]
    if any(col != source_col for _, col in sevens):
        raise ValueError("color-7 source is not vertical")
    bottom_row = max(row for row, _ in sevens)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        reach = bottom_row - row
        if reach < 0:
            continue
        for col in range(width):
            distance = abs(col - source_col)
            if distance <= reach:
                output[row][col] = 7 if distance % 2 == 0 else 8
    return output
