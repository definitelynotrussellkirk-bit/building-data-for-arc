def solve(grid):
    points = [
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == 1
    ]
    if len(points) != 2:
        raise ValueError(f"expected exactly two color-1 cells, got {len(points)}")
    (r0, c0), (r1, c1) = points
    height = abs(r1 - r0) + 1
    width = abs(c1 - c0) + 1
    return [[8 for _ in range(width)] for _ in range(height)]
