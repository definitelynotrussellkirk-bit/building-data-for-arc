def solve(grid):
    """Replace each horizontal endpoint pair by an 8-colored open interval."""
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        markers = [column for column, value in enumerate(row) if value != 0]
        if len(markers) < 2:
            continue
        left, right = min(markers), max(markers)
        for column in range(left + 1, right):
            if row[column] == 0:
                output[row_index][column] = 8
    return output
