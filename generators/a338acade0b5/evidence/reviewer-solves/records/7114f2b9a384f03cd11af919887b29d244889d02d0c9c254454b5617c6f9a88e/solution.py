def solve(grid):
    points = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value != 0
    ]
    if len(points) != 2:
        raise ValueError("expected exactly two nonzero endpoints")
    (row_a, column_a), (row_b, column_b) = points
    length = max(abs(row_b - row_a), abs(column_b - column_a)) + 1
    return [[8] * length]
