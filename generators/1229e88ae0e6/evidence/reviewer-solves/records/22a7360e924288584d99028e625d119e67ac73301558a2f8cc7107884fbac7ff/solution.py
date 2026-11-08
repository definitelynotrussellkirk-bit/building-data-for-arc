def solve(grid):
    """Translate the nonzero bounding box to the grid center."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not occupied:
        return [list(row) for row in grid]

    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(col for _, col in occupied)
    right = max(col for _, col in occupied)

    box_height = bottom - top + 1
    box_width = right - left + 1
    target_top = (height - box_height) // 2
    target_left = (width - box_width) // 2
    row_shift = target_top - top
    col_shift = target_left - left

    result = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in occupied:
        result[row + row_shift][col + col_shift] = grid[row][col]
    return result
