def solve(grid):
    """Count empty rows inside the gray U and draw that many spiral cells."""
    gray = 5
    cyan = 8

    # The bottom of the U is the row with the longest horizontal gray bar.
    bottom = max(range(len(grid)), key=lambda r: sum(cell == gray for cell in grid[r]))
    gray_columns = [c for c, cell in enumerate(grid[bottom]) if cell == gray]
    left, right = min(gray_columns), max(gray_columns)

    # Both vertical walls begin on the same row; the top is open.
    top = min(
        r
        for r in range(bottom)
        if grid[r][left] == gray and grid[r][right] == gray
    )

    empty_rows = sum(
        not any(grid[r][c] == cyan for c in range(left + 1, right))
        for r in range(top, bottom)
    )

    spiral = [
        (0, 0), (0, 1), (0, 2),
        (1, 2), (2, 2), (2, 1),
        (2, 0), (1, 0), (1, 1),
    ]
    output = [[0, 0, 0] for _ in range(3)]
    for r, c in spiral[: min(empty_rows, len(spiral))]:
        output[r][c] = cyan
    return output
