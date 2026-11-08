def solve(grid):
    occupied = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value != 0
    ]
    if not occupied:
        return []

    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(column for _, column in occupied)
    right = max(column for _, column in occupied)

    height = bottom - top + 1
    width = right - left + 1
    return [
        row[left : left + width // 2]
        for row in grid[top : top + height // 2]
    ]
