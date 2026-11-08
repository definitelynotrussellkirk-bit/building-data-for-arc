def solve(grid):
    """Extend a 2x2 colored stamp along the diagonals selected by red cells."""
    height = len(grid)
    width = len(grid[0])

    marked = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    ]
    top = min(row for row, _, _ in marked)
    left = min(col for _, col, _ in marked)
    paint = next(value for _, _, value in marked if value != 2)

    direction_for_corner = {
        (0, 0): (-1, -1),
        (0, 1): (-1, 1),
        (1, 0): (1, -1),
        (1, 1): (1, 1),
    }
    directions = [
        direction_for_corner[(row - top, col - left)]
        for row, col, value in marked
        if value == 2
    ]

    result = [[0 for _ in range(width)] for _ in range(height)]
    for delta_row, delta_col in directions:
        for step in range(max(height, width) + 2):
            stamp_top = top + step * delta_row
            stamp_left = left + step * delta_col
            visible = False
            for row_offset in (0, 1):
                for col_offset in (0, 1):
                    row = stamp_top + row_offset
                    col = stamp_left + col_offset
                    if 0 <= row < height and 0 <= col < width:
                        result[row][col] = paint
                        visible = True
            if not visible:
                break

    return result
