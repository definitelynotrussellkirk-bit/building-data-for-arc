def solve(grid):
    """Center the nonzero pattern's bounding box, preserving all cell values."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    occupied = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    ]

    # The examples always contain a foreground pattern.  Returning an unchanged
    # copy is the least surprising behavior for an empty input.
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
